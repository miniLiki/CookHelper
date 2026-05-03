"""Run retrieval-only evaluation with forced strategy routing."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from eval.rag_eval.metrics import hit_at_k, ndcg_at_k, precision_recall_f1_at_k, unique_preserve_order
from eval.rag_eval.report import generate_reports

logger = logging.getLogger(__name__)
SUPPORTED_STRATEGIES = {"hybrid_traditional", "graph_rag", "combined"}


def load_evalset(path: Path) -> List[dict]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def load_recipe_name_to_ids(nodes_csv: Path) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = {}
    with nodes_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_id = (row.get("nodeId") or "").strip()
            label = (row.get("labels") or "").strip()
            name = (row.get("name") or "").strip()
            if label != "Recipe" or node_id < "200000000" or not name:
                continue
            key = name.strip().lower()
            mapping.setdefault(key, []).append(node_id)
    return mapping


def parse_ks(raw_ks: str) -> List[int]:
    ks = [int(item.strip()) for item in raw_ks.split(",") if item.strip()]
    if not ks:
        raise ValueError("ks cannot be empty")
    if any(k <= 0 for k in ks):
        raise ValueError("all k values must be > 0")
    return ks


def extract_recipe_ids_from_docs(docs: Sequence, name_to_ids: Dict[str, List[str]]) -> List[str]:
    recipe_ids: List[str] = []

    for doc in docs:
        metadata = getattr(doc, "metadata", {}) or {}

        for key in ("node_id", "parent_id", "primary_recipe_id"):
            value = metadata.get(key)
            if isinstance(value, str) and value.startswith("2"):
                recipe_ids.append(value)

        value = metadata.get("recipe_node_ids")
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.startswith("2"):
                    recipe_ids.append(item)

        recipe_name = metadata.get("recipe_name")
        if isinstance(recipe_name, str):
            mapped = name_to_ids.get(recipe_name.strip().lower(), [])
            recipe_ids.extend(mapped)

    return unique_preserve_order(recipe_ids)


def extract_chunk_ids_from_docs(docs: Sequence) -> List[str]:
    chunk_ids: List[str] = []
    for doc in docs:
        metadata = getattr(doc, "metadata", {}) or {}
        chunk_id = metadata.get("chunk_id")
        if isinstance(chunk_id, str) and chunk_id:
            chunk_ids.append(chunk_id)
    return unique_preserve_order(chunk_ids)


def build_doc_summaries(docs: Sequence, limit: int = 5) -> List[dict]:
    summaries: List[dict] = []
    for doc in docs[:limit]:
        metadata = getattr(doc, "metadata", {}) or {}
        summaries.append(
            {
                "recipe_name": metadata.get("recipe_name", ""),
                "node_id": metadata.get("node_id", ""),
                "chunk_id": metadata.get("chunk_id", ""),
                "route_strategy": metadata.get("route_strategy", ""),
                "search_type": metadata.get("search_type", metadata.get("search_method", "")),
            }
        )
    return summaries


def _simple_keyword_extract(query: str) -> tuple[List[str], List[str]]:
    """Fast heuristic keyword extractor used in eval fast mode."""
    tokens = [tok.strip() for tok in re.split(r"[\\s,，。？?！!、]+", query) if tok.strip()]
    if not tokens:
        return [query], []
    return tokens[:3], tokens[3:6]


def enable_fast_eval_mode(rag_system) -> None:
    """Disable LLM parsing in retrieval modules to speed up large-scale eval."""
    try:
        from rag_modules.graph_rag_retrieval import GraphQuery, QueryType
    except Exception:
        return

    rag_system.traditional_retrieval.extract_query_keywords = _simple_keyword_extract

    def _fast_understand(query: str):
        return GraphQuery(
            query_type=QueryType.SUBGRAPH,
            source_entities=[query],
            target_entities=[],
            relation_types=[],
            max_depth=2,
            max_nodes=50,
            constraints={},
        )

    rag_system.graph_rag_retrieval.understand_graph_query = _fast_understand


def evaluate_run(
    example: dict,
    strategy: str,
    pred_recipe_ids: Sequence[str],
    pred_chunk_ids: Sequence[str],
    ks: Iterable[int],
) -> dict:
    metrics: Dict[str, float | None] = {}
    question_type = example["question_type"]

    if question_type == "closed":
        gold_recipe_ids = example.get("gold_recipe_ids", [])
        for k in ks:
            prf = precision_recall_f1_at_k(pred_recipe_ids, gold_recipe_ids, k)
            metrics[f"closed_recipe_precision@{k}"] = prf["precision"]
            metrics[f"closed_recipe_recall@{k}"] = prf["recall"]
            metrics[f"closed_recipe_f1@{k}"] = prf["f1"]

        minimal_support = example.get("minimal_support_chunk_ids", [])
        if strategy == "graph_rag":
            for k in ks:
                metrics[f"closed_chunk_precision@{k}"] = None
                metrics[f"closed_chunk_recall@{k}"] = None
                metrics[f"closed_chunk_f1@{k}"] = None
        elif minimal_support:
            for k in ks:
                prf = precision_recall_f1_at_k(pred_chunk_ids, minimal_support, k)
                metrics[f"closed_chunk_precision@{k}"] = prf["precision"]
                metrics[f"closed_chunk_recall@{k}"] = prf["recall"]
                metrics[f"closed_chunk_f1@{k}"] = prf["f1"]
        else:
            for k in ks:
                metrics[f"closed_chunk_precision@{k}"] = None
                metrics[f"closed_chunk_recall@{k}"] = None
                metrics[f"closed_chunk_f1@{k}"] = None

    elif question_type == "open":
        preferred = example.get("preferred_recipe_ids", [])
        acceptable = example.get("acceptable_recipe_ids", [])

        for k in ks:
            metrics[f"open_hit_preferred@{k}"] = hit_at_k(pred_recipe_ids, preferred, k)
            metrics[f"open_hit_acceptable@{k}"] = hit_at_k(pred_recipe_ids, acceptable, k)
            metrics[f"open_ndcg@{k}"] = ndcg_at_k(pred_recipe_ids, preferred, acceptable, k)

            # 次级指标：preferred-only P/R/F1
            prf = precision_recall_f1_at_k(pred_recipe_ids, preferred, k)
            metrics[f"open_preferred_precision@{k}"] = prf["precision"]
            metrics[f"open_preferred_recall@{k}"] = prf["recall"]
            metrics[f"open_preferred_f1@{k}"] = prf["f1"]

    # 预留 grounded chunk 指标位
    for k in ks:
        metrics[f"grounded_chunk_precision@{k}"] = None
        metrics[f"grounded_chunk_recall@{k}"] = None
        metrics[f"grounded_chunk_f1@{k}"] = None

    return metrics


def run_evaluation(args):
    try:
        from main import AdvancedGraphRAGSystem
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "无法导入运行依赖。请先安装 requirements.txt 中依赖（至少 python-dotenv 等），再执行评测。"
        ) from exc

    ks = parse_ks(args.ks)
    evalset = load_evalset(args.evalset)

    if len(evalset) != 120:
        logger.warning("评测集大小不是120，当前为 %s", len(evalset))

    name_to_ids = load_recipe_name_to_ids(args.nodes_csv)

    rag_system = AdvancedGraphRAGSystem()
    rag_system.initialize_system()
    rag_system.build_knowledge_base()
    if args.fast_no_llm_parse:
        enable_fast_eval_mode(rag_system)
        logger.info("已启用 fast-no-llm-parse 模式（评测加速）")

    strategies = [item.strip() for item in args.strategies.split(",") if item.strip()]
    invalid = [s for s in strategies if s not in SUPPORTED_STRATEGIES]
    if invalid:
        raise ValueError(f"invalid strategies: {invalid}")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "raw_runs.jsonl"

    with raw_path.open("w", encoding="utf-8") as f:
        for example in evalset:
            for strategy in strategies:
                docs, analysis = rag_system.query_router.route_query(
                    query=example["query"],
                    top_k=args.top_k,
                    force_strategy=strategy,
                )

                pred_recipe_ids = extract_recipe_ids_from_docs(docs, name_to_ids)
                pred_chunk_ids = extract_chunk_ids_from_docs(docs)

                run_metrics = evaluate_run(
                    example=example,
                    strategy=strategy,
                    pred_recipe_ids=pred_recipe_ids,
                    pred_chunk_ids=pred_chunk_ids,
                    ks=ks,
                )

                record = {
                    "qid": example["qid"],
                    "question_type": example["question_type"],
                    "query": example["query"],
                    "strategy": strategy,
                    "top_k": args.top_k,
                    "fast_no_llm_parse": bool(args.fast_no_llm_parse),
                    "recommended_strategy": analysis.recommended_strategy.value,
                    "pred_recipe_ids": pred_recipe_ids,
                    "pred_chunk_ids": pred_chunk_ids,
                    "gold_recipe_ids": example.get("gold_recipe_ids", []),
                    "preferred_recipe_ids": example.get("preferred_recipe_ids", []),
                    "acceptable_recipe_ids": example.get("acceptable_recipe_ids", []),
                    "minimal_support_chunk_ids": example.get("minimal_support_chunk_ids", []),
                    "source_note": example.get("source_note", ""),
                    "doc_summaries": build_doc_summaries(docs, limit=5),
                    "metrics": run_metrics,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    reports = generate_reports(raw_path, output_dir, ks)

    print(f"raw_runs: {raw_path}")
    print(f"metrics_by_strategy: {reports['main_csv']}")
    print(f"closed_chunk_appendix: {reports['appendix_csv']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run retrieval evaluation")
    parser.add_argument("--evalset", type=Path, default=Path("eval/rag_eval/evalset_v1_120.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("eval/rag_eval/results"))
    parser.add_argument("--nodes-csv", type=Path, default=Path("data/cypher/nodes.csv"))
    parser.add_argument("--strategies", type=str, default="hybrid_traditional,graph_rag,combined")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--ks", type=str, default="1,3,5")
    parser.add_argument(
        "--fast-no-llm-parse",
        action="store_true",
        help="Disable LLM parsing calls in retrieval modules for faster large-scale evaluation.",
    )

    run_evaluation(parser.parse_args())

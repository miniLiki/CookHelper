"""Reporting utilities for retrieval evaluation outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from .metrics import mean_or_none


def _load_jsonl(path: Path) -> List[dict]:
    records: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _mean_metric(group: Sequence[dict], metric_name: str):
    values = [run.get("metrics", {}).get(metric_name) for run in group]
    return mean_or_none(values)


def _write_csv(path: Path, rows: List[dict], fieldnames: List[str]):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value, na_for_none: bool = False):
    if value is None:
        return "N/A" if na_for_none else ""
    return f"{value:.6f}"


def generate_reports(raw_runs_path: Path, output_dir: Path, ks: Iterable[int]) -> Dict[str, Path]:
    runs = _load_jsonl(raw_runs_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    ks = list(ks)

    grouped = defaultdict(list)
    for run in runs:
        grouped[(run["strategy"], run["question_type"])].append(run)

    strategies = sorted({run["strategy"] for run in runs})
    question_types = ["closed", "open"]

    # Main metrics table
    main_rows: List[dict] = []
    for strategy in strategies:
        for qtype in question_types:
            group = grouped.get((strategy, qtype), [])
            if not group:
                continue

            row = {
                "strategy": strategy,
                "question_type": qtype,
                "count": len(group),
            }

            if qtype == "closed":
                for k in ks:
                    row[f"recipe_precision@{k}"] = _fmt(_mean_metric(group, f"closed_recipe_precision@{k}"))
                    row[f"recipe_recall@{k}"] = _fmt(_mean_metric(group, f"closed_recipe_recall@{k}"))
                    row[f"recipe_f1@{k}"] = _fmt(_mean_metric(group, f"closed_recipe_f1@{k}"))
            else:
                for k in ks:
                    row[f"hit_preferred@{k}"] = _fmt(_mean_metric(group, f"open_hit_preferred@{k}"))
                    row[f"hit_acceptable@{k}"] = _fmt(_mean_metric(group, f"open_hit_acceptable@{k}"))
                    row[f"ndcg@{k}"] = _fmt(_mean_metric(group, f"open_ndcg@{k}"))
                    row[f"preferred_precision@{k}"] = _fmt(_mean_metric(group, f"open_preferred_precision@{k}"))
                    row[f"preferred_recall@{k}"] = _fmt(_mean_metric(group, f"open_preferred_recall@{k}"))
                    row[f"preferred_f1@{k}"] = _fmt(_mean_metric(group, f"open_preferred_f1@{k}"))

            main_rows.append(row)

    main_fields = ["strategy", "question_type", "count"]
    for k in ks:
        main_fields.extend([f"recipe_precision@{k}", f"recipe_recall@{k}", f"recipe_f1@{k}"])
    for k in ks:
        main_fields.extend(
            [
                f"hit_preferred@{k}",
                f"hit_acceptable@{k}",
                f"ndcg@{k}",
                f"preferred_precision@{k}",
                f"preferred_recall@{k}",
                f"preferred_f1@{k}",
            ]
        )

    main_csv = output_dir / "metrics_by_strategy.csv"
    _write_csv(main_csv, main_rows, main_fields)

    # Closed chunk appendix
    appendix_rows: List[dict] = []
    for strategy in strategies:
        group = grouped.get((strategy, "closed"), [])
        if not group:
            continue

        support_group = [
            run
            for run in group
            if isinstance(run.get("minimal_support_chunk_ids"), list)
            and len(run["minimal_support_chunk_ids"]) > 0
        ]

        row = {
            "strategy": strategy,
            "question_type": "closed",
            "count": len(group),
            "support_labeled_count": len(support_group),
        }

        for k in ks:
            p_metric = f"closed_chunk_precision@{k}"
            r_metric = f"closed_chunk_recall@{k}"
            f_metric = f"closed_chunk_f1@{k}"

            p_val = _mean_metric(support_group, p_metric) if support_group else None
            r_val = _mean_metric(support_group, r_metric) if support_group else None
            f_val = _mean_metric(support_group, f_metric) if support_group else None

            is_graph = strategy == "graph_rag"
            row[f"chunk_precision@{k}"] = _fmt(p_val, na_for_none=is_graph)
            row[f"chunk_recall@{k}"] = _fmt(r_val, na_for_none=is_graph)
            row[f"chunk_f1@{k}"] = _fmt(f_val, na_for_none=is_graph)

            # 预留 grounded chunk 指标位
            row[f"grounded_chunk_precision@{k}"] = ""
            row[f"grounded_chunk_recall@{k}"] = ""
            row[f"grounded_chunk_f1@{k}"] = ""

        appendix_rows.append(row)

    appendix_fields = ["strategy", "question_type", "count", "support_labeled_count"]
    for k in ks:
        appendix_fields.extend([f"chunk_precision@{k}", f"chunk_recall@{k}", f"chunk_f1@{k}"])
    for k in ks:
        appendix_fields.extend(
            [
                f"grounded_chunk_precision@{k}",
                f"grounded_chunk_recall@{k}",
                f"grounded_chunk_f1@{k}",
            ]
        )

    appendix_csv = output_dir / "closed_chunk_appendix.csv"
    _write_csv(appendix_csv, appendix_rows, appendix_fields)

    return {
        "main_csv": main_csv,
        "appendix_csv": appendix_csv,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate retrieval evaluation reports")
    parser.add_argument("--raw-runs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("eval/rag_eval/results"))
    parser.add_argument("--ks", type=str, default="1,3,5")
    args = parser.parse_args()

    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
    outputs = generate_reports(args.raw_runs, args.output_dir, ks)

    print(f"metrics_by_strategy: {outputs['main_csv']}")
    print(f"closed_chunk_appendix: {outputs['appendix_csv']}")


if __name__ == "__main__":
    main()

"""Analyze retrieval error cases using top-k miss rules.

Rules:
- closed_miss: none of gold_recipe_ids appears in top-k predictions
- open_miss_both: neither preferred nor acceptable appears in top-k predictions
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


def _load_jsonl(path: Path) -> List[dict]:
    records: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _topk(items: Sequence[str], k: int) -> List[str]:
    if k <= 0:
        return []
    # keep order and unique
    seen = set()
    out: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
        if len(out) >= k:
            break
    return out


def _has_any_overlap(a: Iterable[str], b: Iterable[str]) -> bool:
    b_set = set(b)
    return any(item in b_set for item in a)


def classify_failure(run: dict, top_k: int) -> str | None:
    question_type = run.get("question_type")
    pred = _topk(run.get("pred_recipe_ids", []), top_k)

    if question_type == "closed":
        gold = run.get("gold_recipe_ids", [])
        if gold and not _has_any_overlap(pred, gold):
            return "closed_miss"
        return None

    if question_type == "open":
        preferred = run.get("preferred_recipe_ids", [])
        acceptable = run.get("acceptable_recipe_ids", [])
        hit_pref = _has_any_overlap(pred, preferred)
        hit_acc = _has_any_overlap(pred, acceptable)
        if (preferred or acceptable) and (not hit_pref) and (not hit_acc):
            return "open_miss_both"
        return None

    return None


def analyze_errors(raw_runs: Path, output_dir: Path, top_k: int) -> Dict[str, Path]:
    runs = _load_jsonl(raw_runs)
    output_dir.mkdir(parents=True, exist_ok=True)

    error_rows: List[dict] = []

    total_by_strategy = defaultdict(int)
    fail_by_strategy = defaultdict(int)
    qtype_fail_by_strategy = defaultdict(lambda: defaultdict(int))

    for run in runs:
        strategy = run.get("strategy", "unknown")
        qtype = run.get("question_type", "unknown")
        total_by_strategy[strategy] += 1

        reason = classify_failure(run, top_k)
        if reason is None:
            continue

        fail_by_strategy[strategy] += 1
        qtype_fail_by_strategy[strategy][qtype] += 1

        error_rows.append(
            {
                "qid": run.get("qid", ""),
                "question_type": qtype,
                "query": run.get("query", ""),
                "strategy": strategy,
                "top_k": top_k,
                "pred_recipe_ids": run.get("pred_recipe_ids", []),
                "gold_recipe_ids": run.get("gold_recipe_ids", []),
                "preferred_recipe_ids": run.get("preferred_recipe_ids", []),
                "acceptable_recipe_ids": run.get("acceptable_recipe_ids", []),
                "doc_summaries": run.get("doc_summaries", [])[:5],
                "failure_reason": reason,
            }
        )

    error_jsonl = output_dir / "error_cases_topk_miss.jsonl"
    with error_jsonl.open("w", encoding="utf-8") as f:
        for row in error_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    error_csv = output_dir / "error_cases_topk_miss.csv"
    fieldnames = [
        "qid",
        "question_type",
        "query",
        "strategy",
        "top_k",
        "pred_recipe_ids",
        "gold_recipe_ids",
        "preferred_recipe_ids",
        "acceptable_recipe_ids",
        "doc_summaries",
        "failure_reason",
    ]
    with error_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in error_rows:
            row_dump = dict(row)
            # serialize nested fields for CSV
            for key in (
                "pred_recipe_ids",
                "gold_recipe_ids",
                "preferred_recipe_ids",
                "acceptable_recipe_ids",
                "doc_summaries",
            ):
                row_dump[key] = json.dumps(row_dump[key], ensure_ascii=False)
            writer.writerow(row_dump)

        # summary section
        writer.writerow({})
        writer.writerow({"qid": "#summary", "query": "strategy,fail_count,total_count,fail_rate,closed_fail,open_fail"})
        for strategy in sorted(total_by_strategy.keys()):
            total = total_by_strategy[strategy]
            fail = fail_by_strategy[strategy]
            rate = (fail / total) if total else 0.0
            closed_fail = qtype_fail_by_strategy[strategy].get("closed", 0)
            open_fail = qtype_fail_by_strategy[strategy].get("open", 0)
            writer.writerow(
                {
                    "qid": strategy,
                    "question_type": fail,
                    "query": total,
                    "strategy": f"{rate:.6f}",
                    "top_k": closed_fail,
                    "pred_recipe_ids": open_fail,
                }
            )

    summary_json = output_dir / "error_cases_topk_miss_summary.json"
    summary = {
        "top_k": top_k,
        "total_runs": len(runs),
        "total_errors": len(error_rows),
        "by_strategy": {},
    }
    for strategy in sorted(total_by_strategy.keys()):
        total = total_by_strategy[strategy]
        fail = fail_by_strategy[strategy]
        summary["by_strategy"][strategy] = {
            "fail_count": fail,
            "total_count": total,
            "fail_rate": (fail / total) if total else 0.0,
            "closed_fail": qtype_fail_by_strategy[strategy].get("closed", 0),
            "open_fail": qtype_fail_by_strategy[strategy].get("open", 0),
        }

    with summary_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return {
        "error_jsonl": error_jsonl,
        "error_csv": error_csv,
        "summary_json": summary_json,
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze top-k miss error cases")
    parser.add_argument("--raw-runs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("eval/rag_eval/results"))
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    outputs = analyze_errors(args.raw_runs, args.output_dir, args.top_k)
    print(f"error_cases_jsonl: {outputs['error_jsonl']}")
    print(f"error_cases_csv: {outputs['error_csv']}")
    print(f"summary_json: {outputs['summary_json']}")


if __name__ == "__main__":
    main()

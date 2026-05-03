"""RAG retrieval evaluation metrics."""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence


def unique_preserve_order(values: Sequence[str]) -> List[str]:
    """Return de-duplicated values while preserving order."""
    seen = set()
    deduped: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def precision_recall_f1_at_k(predictions: Sequence[str], gold: Iterable[str], k: int) -> Dict[str, float]:
    """Compute P/R/F1@k for an ordered ranked list."""
    if k <= 0:
        raise ValueError("k must be > 0")

    pred_k = unique_preserve_order(list(predictions))[:k]
    gold_set = set(gold)

    hit_count = sum(1 for item in pred_k if item in gold_set)
    precision = hit_count / k
    recall = hit_count / len(gold_set) if gold_set else 0.0
    f1 = 0.0 if (precision + recall) == 0 else (2.0 * precision * recall) / (precision + recall)

    return {
        "hits": float(hit_count),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def hit_at_k(predictions: Sequence[str], targets: Iterable[str], k: int) -> float:
    """Compute hit@k, where hit is 1 if any target appears in top-k predictions."""
    if k <= 0:
        raise ValueError("k must be > 0")

    pred_k = unique_preserve_order(list(predictions))[:k]
    target_set = set(targets)
    if not target_set:
        return 0.0
    return 1.0 if any(item in target_set for item in pred_k) else 0.0


def ndcg_at_k(
    predictions: Sequence[str],
    preferred: Iterable[str],
    acceptable: Iterable[str],
    k: int,
    preferred_gain: float = 2.0,
    acceptable_gain: float = 1.0,
) -> float:
    """Compute nDCG@k with two-level relevance labels."""
    if k <= 0:
        raise ValueError("k must be > 0")

    pred_k = unique_preserve_order(list(predictions))[:k]

    preferred_set = set(preferred)
    acceptable_set = set(acceptable) - preferred_set

    relevance_map = {item: preferred_gain for item in preferred_set}
    relevance_map.update({item: acceptable_gain for item in acceptable_set})

    def _dcg(scores: Sequence[float]) -> float:
        value = 0.0
        for idx, score in enumerate(scores):
            value += score / math.log2(idx + 2)
        return value

    gains = [relevance_map.get(item, 0.0) for item in pred_k]
    dcg = _dcg(gains)

    ideal = [preferred_gain] * len(preferred_set) + [acceptable_gain] * len(acceptable_set)
    ideal = sorted(ideal, reverse=True)[:k]
    idcg = _dcg(ideal)

    if idcg == 0:
        return 0.0
    return dcg / idcg


def mean_or_none(values: Sequence[float | None]) -> float | None:
    """Average non-None values; return None if empty."""
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)

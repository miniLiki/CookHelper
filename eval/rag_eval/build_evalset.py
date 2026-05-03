"""Build a 120-query retrieval evaluation set for this repository.

Output schema per line (JSONL):
- qid
- question_type: closed | open
- query
- gold_recipe_ids (required for closed)
- preferred_recipe_ids (required for open)
- acceptable_recipe_ids (required for open)
- minimal_support_chunk_ids (optional for closed, default empty)
- source_note
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


CLOSED_TEMPLATES = [
    "我想做{recipe_name}",
    "给我{recipe_name}的做法",
    "怎么做{recipe_name}",
    "请直接给出{recipe_name}菜谱",
    "我今天想吃{recipe_name}，怎么做？",
    "帮我找一下{recipe_name}这道菜",
]

OPEN_TEMPLATES = [
    "我现在有{ingredient}可以做什么菜？",
    "家里有{ingredient}，推荐几道菜",
    "以{ingredient}为主能做哪些家常菜？",
    "如果只看{ingredient}，你会推荐什么菜？",
    "{ingredient}可以做哪些简单菜？",
]


def load_nodes(nodes_csv: Path):
    recipes: Dict[str, Dict[str, str]] = {}
    ingredients: Dict[str, Dict[str, str]] = {}

    with nodes_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_id = (row.get("nodeId") or "").strip()
            label = (row.get("labels") or "").strip()
            name = (row.get("name") or "").strip()

            if not node_id or not name:
                continue

            if label == "Recipe" and node_id >= "200000000" and name != "菜谱":
                recipes[node_id] = {
                    "name": name,
                    "category": (row.get("category") or "").strip() or "未知",
                }
            elif label == "Ingredient" and node_id >= "200000000":
                ingredients[node_id] = {
                    "name": name,
                    "category": (row.get("category") or "").strip() or "未知",
                }

    return recipes, ingredients


def load_requires_relationships(
    relationships_csv: Path,
    ingredients: Dict[str, Dict[str, str]],
):
    recipe_to_ingredients: Dict[str, Set[str]] = defaultdict(set)
    ingredient_name_to_recipes: Dict[str, Set[str]] = defaultdict(set)

    with relationships_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("relationshipType") or "").strip() != "801000001":
                continue
            recipe_id = (row.get("startNodeId") or "").strip()
            ingredient_id = (row.get("endNodeId") or "").strip()
            if not recipe_id or not ingredient_id:
                continue
            recipe_to_ingredients[recipe_id].add(ingredient_id)
            ingredient_name = ingredients.get(ingredient_id, {}).get("name")
            if ingredient_name:
                ingredient_name_to_recipes[ingredient_name].add(recipe_id)

    return recipe_to_ingredients, ingredient_name_to_recipes


def build_closed_queries(recipes: Dict[str, Dict[str, str]], count: int, seed: int) -> List[dict]:
    random.seed(seed)

    recipe_ids = sorted(recipes.keys())
    if len(recipe_ids) < count:
        raise ValueError(f"菜谱数量不足，期望至少 {count}，实际 {len(recipe_ids)}")

    sampled = random.sample(recipe_ids, count)
    sampled.sort()

    records = []
    for idx, recipe_id in enumerate(sampled, start=1):
        recipe_name = recipes[recipe_id]["name"]
        template = CLOSED_TEMPLATES[(idx - 1) % len(CLOSED_TEMPLATES)]
        records.append(
            {
                "qid": f"closed_{idx:03d}",
                "question_type": "closed",
                "query": template.format(recipe_name=recipe_name),
                "gold_recipe_ids": [recipe_id],
                "preferred_recipe_ids": [],
                "acceptable_recipe_ids": [],
                "minimal_support_chunk_ids": [],
                "source_note": f"recipe_id={recipe_id}, recipe_name={recipe_name}",
            }
        )
    return records


def _pick_preferred_and_acceptable(
    ingredient_name: str,
    recipe_ids: List[str],
    recipes: Dict[str, Dict[str, str]],
) -> tuple[list[str], list[str]]:
    name_match = [rid for rid in recipe_ids if ingredient_name in recipes[rid]["name"]]

    if name_match:
        preferred = name_match[: min(8, len(name_match))]
    else:
        preferred_size = max(1, min(6, len(recipe_ids) // 3))
        preferred = recipe_ids[:preferred_size]

    preferred_set = set(preferred)
    remainder = [rid for rid in recipe_ids if rid not in preferred_set]
    acceptable = remainder[: min(12, len(remainder))]

    if not acceptable and remainder:
        acceptable = [remainder[0]]

    return preferred, acceptable


def build_open_queries(
    recipes: Dict[str, Dict[str, str]],
    ingredient_name_to_recipes: Dict[str, Set[str]],
    count: int,
) -> List[dict]:
    candidate_ingredients: List[tuple[str, int]] = []
    for ingredient_name, recipe_ids in ingredient_name_to_recipes.items():
        total = len(recipe_ids)
        # 过滤过窄/过宽的食材，减少无意义超大集合
        if 4 <= total <= 80:
            candidate_ingredients.append((ingredient_name, total))

    candidate_ingredients.sort(key=lambda x: (-x[1], x[0]))

    if len(candidate_ingredients) < count:
        raise ValueError(
            f"可用开放题食材不足，期望 {count}，实际 {len(candidate_ingredients)}。"
            "可放宽 recipe_count 过滤区间。"
        )

    records = []
    for idx, (ingredient_name, recipe_count) in enumerate(candidate_ingredients[:count], start=1):
        recipe_ids = sorted(ingredient_name_to_recipes[ingredient_name])

        preferred, acceptable = _pick_preferred_and_acceptable(ingredient_name, recipe_ids, recipes)

        template = OPEN_TEMPLATES[(idx - 1) % len(OPEN_TEMPLATES)]
        records.append(
            {
                "qid": f"open_{idx:03d}",
                "question_type": "open",
                "query": template.format(ingredient=ingredient_name),
                "gold_recipe_ids": [],
                "preferred_recipe_ids": preferred,
                "acceptable_recipe_ids": acceptable,
                "minimal_support_chunk_ids": [],
                "source_note": (
                    f"ingredient_name={ingredient_name}, "
                    f"candidate_recipes={recipe_count}, preferred={len(preferred)}, acceptable={len(acceptable)}"
                ),
            }
        )

    return records


def main():
    parser = argparse.ArgumentParser(description="Build retrieval evaluation set")
    parser.add_argument("--nodes-csv", type=Path, default=Path("data/cypher/nodes.csv"))
    parser.add_argument("--relationships-csv", type=Path, default=Path("data/cypher/relationships.csv"))
    parser.add_argument("--output", type=Path, default=Path("eval/rag_eval/evalset_v1_120.jsonl"))
    parser.add_argument("--closed-count", type=int, default=60)
    parser.add_argument("--open-count", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    recipes, ingredients = load_nodes(args.nodes_csv)
    _, ingredient_name_to_recipes = load_requires_relationships(args.relationships_csv, ingredients)

    closed = build_closed_queries(recipes, args.closed_count, args.seed)
    open_ = build_open_queries(recipes, ingredient_name_to_recipes, args.open_count)
    dataset = closed + open_

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"wrote {len(dataset)} examples -> {args.output}")
    print(f"closed: {len(closed)}, open: {len(open_)}")


if __name__ == "__main__":
    main()

import json

from eval.rag_eval.analyze_errors import classify_failure


def test_classify_failure_closed_miss():
    run = {
        "question_type": "closed",
        "pred_recipe_ids": ["201000001", "201000002"],
        "gold_recipe_ids": ["201000999"],
    }
    assert classify_failure(run, 5) == "closed_miss"


def test_classify_failure_open_miss_both():
    run = {
        "question_type": "open",
        "pred_recipe_ids": ["201000001", "201000002"],
        "preferred_recipe_ids": ["201009999"],
        "acceptable_recipe_ids": ["201008888"],
    }
    assert classify_failure(run, 5) == "open_miss_both"


def test_classify_failure_open_hit_preferred():
    run = {
        "question_type": "open",
        "pred_recipe_ids": ["201000001", "201000002"],
        "preferred_recipe_ids": ["201000002"],
        "acceptable_recipe_ids": ["201008888"],
    }
    assert classify_failure(run, 5) is None

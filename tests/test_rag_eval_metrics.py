from langchain_core.documents import Document

from eval.rag_eval.metrics import hit_at_k, ndcg_at_k, precision_recall_f1_at_k
from rag_modules.intelligent_query_router import IntelligentQueryRouter, SearchStrategy


class DummyTraditionalRetriever:
    def __init__(self):
        self.called = 0

    def hybrid_search(self, query, top_k):
        self.called += 1
        return [Document(page_content="ok", metadata={"node_id": "201000001"})]


class DummyGraphRetriever:
    def __init__(self, fail=False):
        self.fail = fail
        self.called = 0

    def graph_rag_search(self, query, top_k):
        self.called += 1
        if self.fail:
            raise RuntimeError("graph error")
        return [Document(page_content="graph", metadata={"recipe_name": "白灼虾"})]


class DummyLLMClient:
    pass


class DummyConfig:
    llm_model = "dummy"


def test_precision_recall_f1_with_duplicates():
    pred = ["a", "a", "b", "c"]
    gold = ["a", "d"]
    result = precision_recall_f1_at_k(pred, gold, 3)

    assert result["precision"] == 1 / 3
    assert result["recall"] == 1 / 2
    assert round(result["f1"], 6) == round(2 * (1 / 3) * (1 / 2) / ((1 / 3) + (1 / 2)), 6)


def test_hit_and_ndcg_open_metrics():
    pred = ["r1", "r2", "r3"]
    preferred = ["r1"]
    acceptable = ["r3"]

    assert hit_at_k(pred, preferred, 1) == 1.0
    assert hit_at_k(pred, acceptable, 2) == 0.0
    assert 0.0 <= ndcg_at_k(pred, preferred, acceptable, 3) <= 1.0


def test_route_query_force_strategy_no_fallback_when_forced_strategy_fails():
    traditional = DummyTraditionalRetriever()
    graph = DummyGraphRetriever(fail=True)

    router = IntelligentQueryRouter(
        traditional_retrieval=traditional,
        graph_rag_retrieval=graph,
        llm_client=DummyLLMClient(),
        config=DummyConfig(),
    )

    docs, analysis = router.route_query("测试", top_k=5, force_strategy=SearchStrategy.GRAPH_RAG.value)

    assert docs == []
    assert analysis.recommended_strategy == SearchStrategy.GRAPH_RAG
    assert graph.called == 1
    assert traditional.called == 0

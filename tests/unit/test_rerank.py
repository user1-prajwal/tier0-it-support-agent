from app.retrieval.rerank import rerank_hits
from app.retrieval.search import FusedHit


def hit(chunk_id, heading="H", text="t"):
    return FusedHit(
        chunk_id=chunk_id, document_id=1, title="T", source_uri="a.md",
        heading_path=heading, text=text, score=0.0, dense_rank=None, fulltext_rank=None,
    )


class ScriptedReranker:
    model_name = "scripted"

    def __init__(self, scores):
        self._scores = scores
        self.seen = None

    def score(self, query, texts):
        self.seen = (query, texts)
        return self._scores


def test_rerank_orders_by_score_keeps_the_top_and_breaks_ties_by_input_order():
    hits = [hit(1), hit(2), hit(3), hit(4)]
    reranker = ScriptedReranker([0.1, 2.0, 0.1, -3.0])  # chunks 1 and 3 tie

    result = rerank_hits(reranker, "q", hits, keep=3)

    assert [h.chunk_id for h in result] == [2, 1, 3]  # 4 is dropped, 1 stays before 3
    assert [h.rerank_score for h in result] == [2.0, 0.1, 0.1]


def test_the_reranker_reads_heading_and_text_and_is_not_called_for_nothing():
    reranker = ScriptedReranker([0.0])
    candidate = hit(1, heading="Password reset > Steps", text="Open the portal.")
    rerank_hits(reranker, "how do I reset", [candidate], keep=5)
    assert reranker.seen == ("how do I reset", ["Password reset > Steps\nOpen the portal."])

    unused = ScriptedReranker([])
    assert rerank_hits(unused, "q", [], keep=5) == []
    assert unused.seen is None
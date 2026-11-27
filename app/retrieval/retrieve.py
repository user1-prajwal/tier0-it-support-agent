"""The final retrieval function: permission-filtered hybrid search, then rerank."""

from collections.abc import Sequence

from sqlalchemy import Engine

from app.retrieval.embedder import Embedder
from app.retrieval.rerank import Reranker, rerank_hits
from app.retrieval.search import FusedHit, hybrid_search

CANDIDATES = 20  # fused candidates passed to the reranker (brief: compare 10, 20 and 30)
KEEP = 5  # chunks kept for the prompt


def retrieve(
    engine: Engine,
    embedder: Embedder,
    reranker: Reranker,
    question: str,
    group_ids: Sequence[int],
    *,
    candidates: int = CANDIDATES,
    keep: int = KEEP,
) -> list[FusedHit]:
    hits = hybrid_search(engine, embedder, question, group_ids, limit=candidates)
    return rerank_hits(reranker, question, hits, keep=keep)
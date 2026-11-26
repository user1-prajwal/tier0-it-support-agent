"""Cross-encoder reranking: re-order hybrid candidates by reading each (question, chunk) pair.

Our embedder is a bi-encoder: it embeds the question and each chunk separately and compares the
vectors. A cross-encoder reads the question and the chunk together, so it can notice that an
exact code in the question appears in the chunk. That is slower, so it only sees the few
candidates hybrid search already returned, all of them permission-filtered. It can reorder
those candidates and drop some. It cannot add a chunk.
"""

from dataclasses import replace
from typing import Protocol

from app.retrieval.search import FusedHit


class Reranker(Protocol):
    model_name: str

    def score(self, query: str, texts: list[str]) -> list[float]: ...


class FastEmbedReranker:
    """Real local cross-encoder (ONNX, CPU). Scores are raw logits, not probabilities."""

    def __init__(
        self, model_name: str = "Xenova/ms-marco-MiniLM-L-6-v2", *, cache_dir: str | None = None
    ) -> None:
        # Imported here so tests with a scripted reranker never load onnxruntime.
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self.model_name = model_name
        self._model = TextCrossEncoder(model_name=model_name, cache_dir=cache_dir)

    def score(self, query: str, texts: list[str]) -> list[float]:
        return [float(score) for score in self._model.rerank(query, texts)]


def _pair_text(hit: FusedHit) -> str:
    """The chunk as the reranker reads it: heading path first, so a short chunk has a topic."""
    return f"{hit.heading_path}\n{hit.text}" if hit.heading_path else hit.text


def rerank_hits(
    reranker: Reranker, question: str, hits: list[FusedHit], *, keep: int = 5
) -> list[FusedHit]:
    if not hits:
        return []
    scores = reranker.score(question, [_pair_text(hit) for hit in hits])
    # strict=True: a wrong number of scores must fail loudly, never attach scores to wrong chunks.
    scored = list(zip(hits, scores, strict=True))
    scored.sort(key=lambda pair: -pair[1])  # stable sort: equal scores keep their fused order
    return [replace(hit, rerank_score=score) for hit, score in scored[:keep]]
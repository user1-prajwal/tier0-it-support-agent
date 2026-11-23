"""Embedders turn text into vectors.

HashEmbedder is for TESTS ONLY: a bag-of-words hashing trick that can check our retrieval
logic (filtering, fusion, ordering) but says nothing about real semantic quality.
FastEmbedEmbedder is the real local model used by ingestion and search.
"""

import hashlib
import math
import re
from typing import Protocol

DIMENSIONS = 384  # bge-small-en-v1.5 and HashEmbedder share this, so one column fits both
# The query instruction from the BGE model card. Off by default: Step 7 measures it.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_WORD = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    model_name: str  # stored on every chunk, so a model change is detected, never mixed

    def embed_query(self, text: str) -> list[float]: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


def _unit(vector: list[float]) -> list[float]:
    """Scale to length 1, so a dot product equals cosine similarity."""
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0.0:
        return vector  # no content: a zero vector, because we cannot divide by zero
    return [x / norm for x in vector]


class HashEmbedder:
    model_name = "hash-384-test-only"

    def embed_query(self, text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for word in _WORD.findall(text.lower()):
            # sha256 is stable across runs. Python's built-in hash() is randomised.
            digest = hashlib.sha256(word.encode()).digest()
            vector[int.from_bytes(digest[:4], "big") % DIMENSIONS] += 1.0
        return _unit(vector)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]


class FastEmbedEmbedder:
    """Real embeddings through FastEmbed (ONNX): no GPU, no network after the first download."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        *,
        cache_dir: str | None = None,
        query_prefix: str = "",
    ) -> None:
        # Imported here so code and tests that only use HashEmbedder never load onnxruntime.
        from fastembed import TextEmbedding

        self.model_name = model_name
        self._query_prefix = query_prefix  # an explicit choice, compared in the ablation
        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)

    def embed_query(self, text: str) -> list[float]:
        vector = next(iter(self._model.embed([self._query_prefix + text])))
        return _unit(vector.tolist())

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_unit(vector.tolist()) for vector in self._model.embed(texts)]
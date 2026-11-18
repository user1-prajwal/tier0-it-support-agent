"""Embedders turn text into vectors.

HashEmbedder is for TESTS ONLY. It is a bag-of-words hashing trick, so it can check
our retrieval logic (filtering, fusion, ordering) but says nothing about real
semantic quality. The real embedder (FastEmbed) arrives in Phase 1.
"""

import hashlib
import math
import re
from typing import Protocol

DIMENSIONS = 384  # same size as bge-small-en-v1.5, so one database column fits both

_WORD = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


class HashEmbedder:
    def embed_query(self, text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for word in _WORD.findall(text.lower()):
            # sha256 is stable across runs. Python's built-in hash() is randomised.
            digest = hashlib.sha256(word.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % DIMENSIONS
            vector[index] += 1.0

        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0.0:
            return vector  # no words: a zero vector, because we cannot divide by zero
        return [x / norm for x in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]
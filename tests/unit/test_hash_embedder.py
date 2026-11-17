"""Tests for HashEmbedder.

HashEmbedder is a TEST-ONLY embedder. It checks our retrieval logic (filtering,
fusion, ordering). It says nothing about real semantic quality.
"""

import math
import os
import subprocess
import sys

from app.retrieval.embedder import HashEmbedder


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_vector_has_384_dimensions():
    assert len(HashEmbedder().embed_query("reset my password")) == 384


def test_vector_has_unit_length():
    v = HashEmbedder().embed_query("reset my password")
    assert math.isclose(math.sqrt(dot(v, v)), 1.0, rel_tol=1e-9)


def test_same_text_gives_the_same_vector():
    e = HashEmbedder()
    assert e.embed_query("vpn keeps disconnecting") == e.embed_query("vpn keeps disconnecting")


def test_same_vector_in_a_new_python_process():
    # Python's built-in hash() is randomised per process (PYTHONHASHSEED).
    # If we used it, the same text would get different vectors on each run.
    code = (
        "from app.retrieval.embedder import HashEmbedder; "
        "print(HashEmbedder().embed_query('vpn keeps disconnecting')[:8])"
    )
    outputs = set()
    for seed in ("1", "2", "3"):
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
        )
        outputs.add(result.stdout)
    assert len(outputs) == 1


def test_is_case_insensitive():
    e = HashEmbedder()
    assert e.embed_query("VPN Timeout") == e.embed_query("vpn timeout")


def test_shared_words_score_higher_than_unrelated_text():
    e = HashEmbedder()
    query = e.embed_query("reset my password")
    related = e.embed_query("how to reset a password")
    unrelated = e.embed_query("printer toner replacement")
    assert dot(query, related) > dot(query, unrelated)


def test_text_without_words_gives_a_zero_vector():
    v = HashEmbedder().embed_query("")
    assert len(v) == 384
    assert all(x == 0.0 for x in v)


def test_documents_and_queries_use_the_same_space():
    e = HashEmbedder()
    texts = ["reset password", "vpn timeout"]
    assert e.embed_documents(texts) == [e.embed_query(t) for t in texts]
import pytest

from app.retrieval.fusion import reciprocal_rank_fusion


def test_the_worked_example():
    # Chunk ids: A=1, B=2, C=3, D=4. Dense ranks [A, B, C]. Full-text ranks [B, D, A].
    fused = reciprocal_rank_fusion([[1, 2, 3], [2, 4, 1]])

    assert [chunk_id for chunk_id, _ in fused] == [2, 1, 4, 3]  # B, A, D, C
    scores = dict(fused)
    assert scores[2] == pytest.approx(1 / 62 + 1 / 61)
    assert scores[1] == pytest.approx(1 / 61 + 1 / 63)
    assert scores[4] == pytest.approx(1 / 62)  # found by one arm only: still included
    assert scores[3] == pytest.approx(1 / 63)


def test_ties_are_broken_the_same_way_every_time():
    # Chunks 5 and 7 swap places between the arms, so their scores are exactly equal.
    first = reciprocal_rank_fusion([[5, 7], [7, 5]])
    second = reciprocal_rank_fusion([[7, 5], [5, 7]])

    assert [c for c, _ in first] == [5, 7]
    assert [c for c, _ in second] == [5, 7]
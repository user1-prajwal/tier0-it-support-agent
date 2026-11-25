"""Reciprocal rank fusion (RRF): combine ranked lists from different searches.

A cosine distance and a text-rank score live on unrelated scales, so adding them would need
calibration. RRF uses only each chunk's POSITION in each list, which needs none.
"""

RRF_K = 60  # dampens the lead of rank 1 over rank 2. 60 is the brief's starting value


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = RRF_K) -> list[tuple[int, float]]:
    """rankings: one list of chunk ids per search, best first, each id at most once per list.

    Returns (chunk_id, score) pairs, best first. Equal scores are ordered by chunk id, so
    the result is the same on every run.
    """
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
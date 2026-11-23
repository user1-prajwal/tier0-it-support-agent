"""Retrieval metrics. A 'section' is a (source_uri, heading_path) pair, not a chunk id,
so re-chunking never breaks a label."""

Section = tuple[str, str]


def first_gold_rank(retrieved: list[Section], gold: list[Section]) -> int | None:
    """1-based position of the first retrieved chunk that lies in a gold section."""
    gold_set = set(gold)
    for rank, section in enumerate(retrieved, start=1):
        if section in gold_set:
            return rank
    return None


def recall_at_k(ranks: list[int | None], k: int) -> float:
    """Share of questions whose first gold chunk is within the top k."""
    return sum(1 for r in ranks if r is not None and r <= k) / len(ranks)


def mean_reciprocal_rank(ranks: list[int | None]) -> float:
    """Mean of 1/rank of the first gold chunk. A question that is not found counts as 0."""
    return sum(1 / r for r in ranks if r is not None) / len(ranks)
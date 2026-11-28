"""Retrieval metrics. A 'section' is a (source_uri, heading_path) pair, not a chunk id,
so re-chunking never breaks a label."""

import math

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

def all_gold_in_top_k(retrieved: list[Section], gold: list[Section], k: int) -> bool:
    """True if EVERY gold section appears among the first k retrieved chunks."""
    top = set(retrieved[:k])
    return all(section in top for section in gold)


def compare_ranks(a: list[int | None], b: list[int | None]) -> tuple[int, int, int]:
    """Per question, did method b find the first gold chunk higher, lower or equal to a?

    Returns (better, worse, same) counts for b relative to a. Not found counts as the worst.
    """
    worst = float("inf")
    better = worse = same = 0
    for rank_a, rank_b in zip(a, b, strict=True):
        x = worst if rank_a is None else rank_a
        y = worst if rank_b is None else rank_b
        if y < x:
            better += 1
        elif y > x:
            worse += 1
        else:
            same += 1
    return better, worse, same


def sign_test_p(better: int, worse: int) -> float:
    """Two-sided exact sign test. If two methods were equally good, each question that
    differs would favour either one with probability 1/2. Ties are ignored.

    Our questions are not fully independent (some share a gold section), so this p-value
    is optimistic. It is a guard against over-reading small differences, not proof.
    """
    n = better + worse
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(better, worse) + 1)) / 2**n
    return min(1.0, 2 * tail)
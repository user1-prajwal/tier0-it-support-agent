import pytest

from eval.metrics import all_gold_in_top_k, compare_ranks, sign_test_p


def test_all_gold_sections_must_be_present_within_k():
    a, b, c = ("a.md", "A"), ("b.md", "B"), ("c.md", "C")
    assert all_gold_in_top_k([a, c, b], [a, b], 3) is True
    assert all_gold_in_top_k([a, c, b], [a, b], 2) is False  # b only appears at position 3
    assert all_gold_in_top_k([a, a, a], [a, b], 3) is False  # repeats of a do not cover b


def test_paired_comparison_and_the_sign_test():
    # Ranks of the first correct chunk per question. Lower is better, None = not found.
    better, worse, same = compare_ranks([2, 1, None, 3, 5], [1, 1, 4, 5, None])
    assert (better, worse, same) == (2, 2, 1)  #(2->1) and (None->4) better; (3->5), (5->None) worse

    assert sign_test_p(8, 0) == pytest.approx(2 / 256)  # 8 of 8 in one direction
    assert sign_test_p(5, 5) == 1.0  # an even split shows nothing
    assert sign_test_p(0, 0) == 1.0  # no question differs
    assert sign_test_p(9, 3) == pytest.approx(2 * 299 / 4096)  # (1+12+66+220) / 2**12, doubled
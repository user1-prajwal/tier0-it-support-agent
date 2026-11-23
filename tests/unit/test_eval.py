import json

import pytest

from eval.dataset import QuestionError, missing_gold, parse_questions, split_of
from eval.metrics import first_gold_rank, mean_reciprocal_rank, recall_at_k

GOLD = [{"source_uri": "kb/vpn.md", "heading_path": "VPN > Setup"}]


def record(**overrides):
    base = {
        "id": "q1",
        "category": "single_document",
        "asked_by": "alice@demo.local",
        "question": "How do I set up the VPN?",
        "answerable": True,
        "gold": GOLD,
    }
    return {**base, **overrides}


def to_jsonl(*records):
    return "\n".join(json.dumps(r) for r in records)


def test_metrics_on_a_worked_example():
    a = ("a.md", "A > x")
    ranks = [
        first_gold_rank([("b.md", "B"), a], [a]),  # found at rank 2
        first_gold_rank([a], [a]),  # found at rank 1
        first_gold_rank([("c.md", "C")], [a]),  # not found
    ]
    assert ranks == [2, 1, None]
    assert recall_at_k(ranks, 1) == pytest.approx(1 / 3)
    assert recall_at_k(ranks, 2) == pytest.approx(2 / 3)
    assert mean_reciprocal_rank(ranks) == pytest.approx(0.5)  # (1/2 + 1 + 0) / 3


def test_split_is_deterministic_and_about_seventy_percent_dev():
    assert split_of("q-017") == split_of("q-017")
    splits = [split_of(f"q-{i}") for i in range(2000)]
    assert set(splits) == {"dev", "test"}
    assert 0.65 < splits.count("dev") / len(splits) < 0.75


@pytest.mark.parametrize(
    "records",
    [
        [record(gold=[])],  # answerable with nothing to find would score a silent zero
        [record(answerable=False)],  # not answerable, yet it has a gold label
        [record(asked_by="mallory@demo.local")],  # not a known user
        [record(), record()],  # duplicate id
    ],
    ids=["answerable-without-gold", "unanswerable-with-gold", "unknown-user", "duplicate-id"],
)
def test_bad_question_records_are_rejected(records):
    with pytest.raises(QuestionError):
        parse_questions(to_jsonl(*records))


def test_gold_that_matches_no_ingested_section_is_reported():
    questions = parse_questions(to_jsonl(record()))
    assert missing_gold(questions, known={("kb/vpn.md", "VPN > Setup")}) == []
    # A one-letter typo in a heading path must be caught, not scored as a miss.
    assert missing_gold(questions, known={("kb/vpn.md", "VPN > Setups")}) == [
        ("q1", ("kb/vpn.md", "VPN > Setup"))
    ]
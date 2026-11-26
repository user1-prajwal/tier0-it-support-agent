"""Load and validate the labelled questions (JSONL: one JSON object per line)."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from app.db.demo_users import DEMO_USERS

CATEGORIES = {
    "single_document",
    "multi_chunk",
    "paraphrase",
    "exact_token",
    "unanswerable",
    "permission_pair",
    "injection",
    "tool_selection",
}

# Who may be named in asked_by: the active demo users. Their groups come from the database.
KNOWN_ASKERS = {user.email for user in DEMO_USERS if user.is_active}

# Never change these once questions exist: it would move questions between dev and test.
SPLIT_SEED = "tier0-eval-v1"
DEV_PERCENT = 70

_REQUIRED = {"id", "category", "asked_by", "question", "answerable", "gold"}
_OPTIONAL = {"expected_tool", "notes", "llm_drafted"}


class QuestionError(ValueError):
    """A question record is invalid."""


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    asked_by: str
    question: str
    answerable: bool
    gold: tuple[tuple[str, str], ...]  # (source_uri, heading_path) pairs


def split_of(question_id: str) -> str:
    """'dev' or 'test', decided by the id alone, so adding questions never moves others."""
    digest = hashlib.sha256(f"{SPLIT_SEED}:{question_id}".encode()).hexdigest()
    return "dev" if int(digest, 16) % 100 < DEV_PERCENT else "test"


def load_questions(path: Path) -> list[Question]:
    return parse_questions(path.read_text(encoding="utf-8"))


def parse_questions(text: str) -> list[Question]:
    questions: list[Question] = []
    seen: set[str] = set()
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            question = _parse_record(json.loads(line))
            if question.id in seen:
                raise QuestionError(f"duplicate id {question.id!r}")
        except (json.JSONDecodeError, QuestionError) as exc:
            raise QuestionError(f"line {number}: {exc}") from exc
        seen.add(question.id)
        questions.append(question)
    return questions


def missing_gold(
    questions: list[Question], known: set[tuple[str, str]]
) -> list[tuple[str, tuple[str, str]]]:
    """Gold labels that match no ingested section. Usually a typo in a heading path."""
    return [(q.id, g) for q in questions for g in q.gold if g not in known]


def _parse_record(record: object) -> Question:
    if not isinstance(record, dict):
        raise QuestionError("each line must be a JSON object")
    missing, unknown = _REQUIRED - record.keys(), record.keys() - _REQUIRED - _OPTIONAL
    if missing:
        raise QuestionError(f"missing keys: {sorted(missing)}")
    if unknown:
        raise QuestionError(f"unknown keys: {sorted(unknown)}")

    qid, category, asked_by = record["id"], record["category"], record["asked_by"]
    text, answerable = record["question"], record["answerable"]
    if not isinstance(qid, str) or not qid.strip():
        raise QuestionError("id must be a non-empty string")
    if not isinstance(category, str) or category not in CATEGORIES:
        raise QuestionError(f"category must be one of {sorted(CATEGORIES)}")
    if not isinstance(asked_by, str) or asked_by not in KNOWN_ASKERS:
        raise QuestionError(f"asked_by must be one of {sorted(KNOWN_ASKERS)}")
    if not isinstance(text, str) or not text.strip():
        raise QuestionError("question must be a non-empty string")
    if not isinstance(answerable, bool):
        raise QuestionError("answerable must be true or false")

    gold = _parse_gold(record["gold"])
    if answerable != bool(gold):
        raise QuestionError("answerable questions need gold labels, unanswerable ones none")
    return Question(qid, category, asked_by, text, answerable, gold)


def _parse_gold(gold: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(gold, list):
        raise QuestionError("gold must be a list")
    sections = []
    for item in gold:
        valid = (
            isinstance(item, dict)
            and set(item) == {"source_uri", "heading_path"}
            and all(isinstance(v, str) and v for v in item.values())
        )
        if not valid:
            raise QuestionError(
                'gold entries look like {"source_uri": "...", "heading_path": "..."}'
            )
        sections.append((item["source_uri"], item["heading_path"]))
    return tuple(sections)
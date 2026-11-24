"""Dense (vector) search with the permission filter INSIDE the SQL.

Filtering and ranking happen in one query. A chunk the caller's groups may not read never
reaches ranking, reranking or any prompt. Never filter the results afterwards.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Engine, text

from app.db.vector import to_pgvector

DENSE_SQL = text(
    """
    SELECT c.id AS chunk_id, c.document_id, d.title, d.source_uri, c.heading_path, c.text,
           c.embedding <=> CAST(:qvec AS vector) AS distance
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    WHERE d.status = 'active'
      AND EXISTS (
          SELECT 1 FROM document_acl a
          WHERE a.document_id = d.id
            AND a.group_id = ANY(CAST(:group_ids AS bigint[]))
      )
    ORDER BY distance, c.id
    LIMIT :limit
    """
)


@dataclass(frozen=True)
class Hit:
    chunk_id: int
    document_id: int
    title: str
    source_uri: str
    heading_path: str
    text: str
    distance: float  # cosine distance: 0 is identical, smaller is closer


def dense_search(
    engine: Engine, query_vector: list[float], group_ids: Sequence[int], limit: int = 30
) -> list[Hit]:
    params = {"qvec": to_pgvector(query_vector), "group_ids": list(group_ids), "limit": limit}
    with engine.connect() as conn:
        rows = conn.execute(DENSE_SQL, params).all()
    return [Hit(**row._mapping) for row in rows]


# --- Full-text search -----------------------------------------------------------------

_TERM = re.compile(r"[a-z0-9]+")
MAX_TERMS = 32
MAX_TERM_LENGTH = 64


def build_or_query(text_: str) -> str | None:
    """Convert a question into a safe PostgreSQL full-text search query."""

    terms = [t for t in _TERM.findall(text_.lower()) if len(t) <= MAX_TERM_LENGTH]
    unique = list(dict.fromkeys(terms))[:MAX_TERMS]

    return " | ".join(unique) or None


FULLTEXT_SQL = text(
    """
    SELECT c.id AS chunk_id, c.document_id, d.title, d.source_uri, c.heading_path, c.text,
           ts_rank_cd(c.tsv, q) AS score
    FROM chunks c
    JOIN documents d ON d.id = c.document_id,
         to_tsquery('english', :or_query) q
    WHERE c.tsv @@ q
      AND d.status = 'active'
      AND EXISTS (
          SELECT 1 FROM document_acl a
          WHERE a.document_id = d.id
            AND a.group_id = ANY(CAST(:group_ids AS bigint[]))
      )
    ORDER BY score DESC, c.id
    LIMIT :limit
    """
)


@dataclass(frozen=True)
class FullTextHit:
    chunk_id: int
    document_id: int
    title: str
    source_uri: str
    heading_path: str
    text: str
    score: float


def fulltext_search(
    engine: Engine, question: str, group_ids: Sequence[int], limit: int = 30
) -> list[FullTextHit]:
    or_query = build_or_query(question)

    if or_query is None:
        return []

    params = {
        "or_query": or_query,
        "group_ids": list(group_ids),
        "limit": limit,
    }

    with engine.connect() as conn:
        rows = conn.execute(FULLTEXT_SQL, params).all()

    return [FullTextHit(**row._mapping) for row in rows]

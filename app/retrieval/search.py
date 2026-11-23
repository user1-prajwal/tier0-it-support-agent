"""Dense (vector) search with the permission filter INSIDE the SQL.

Filtering and ranking happen in one query. A chunk the caller's groups may not read never
reaches ranking, reranking or any prompt. Never filter the results afterwards.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Engine, text

from app.db.vector import to_pgvector

DENSE_SQL = text(
    """
    SELECT c.id AS chunk_id, c.document_id, d.title, c.heading_path, c.text,
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
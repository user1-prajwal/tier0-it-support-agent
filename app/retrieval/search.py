"""Dense (vector) search with the permission filter INSIDE the SQL.

Filtering and ranking happen in one query. A chunk the caller's groups may not read never
reaches ranking, reranking or any prompt. Never filter the results afterwards.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Engine, text

from app.db.vector import to_pgvector
from app.retrieval.embedder import Embedder
from app.retrieval.fusion import reciprocal_rank_fusion

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

# plainto_tsquery tokenizes the question with the same parser that built the index (so codes,
# hostnames and emails match) and ignores any query operators in the text. It joins terms
# with AND, so the text form of its result is rewritten with OR. The question is only ever a
# bound parameter and is never pasted into SQL.
FULLTEXT_SQL = text(
    """
    WITH q AS (
        SELECT CAST(
                   replace(
                       CAST(plainto_tsquery('english', CAST(:question AS text)) AS text),
                       ' & ', ' | '
                   ) AS tsquery
               ) AS tsq
    )
    SELECT c.id AS chunk_id, c.document_id, d.title, d.source_uri, c.heading_path, c.text,
           ts_rank_cd(c.tsv, q.tsq) AS score
    FROM q, chunks c
    JOIN documents d ON d.id = c.document_id
    WHERE c.tsv @@ q.tsq
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
    score: float  # ts_rank_cd: larger is better. Not comparable with a dense distance


def fulltext_search(
    engine: Engine, question: str, group_ids: Sequence[int], limit: int = 30
) -> list[FullTextHit]:
    params = {
        # A NUL byte cannot be sent to Postgres as text and would raise, so treat it as a space.
        "question": question.replace("\x00", " "),
        "group_ids": list(group_ids),
        "limit": limit,
    }
    with engine.connect() as conn:
        rows = conn.execute(FULLTEXT_SQL, params).all()
    return [FullTextHit(**row._mapping) for row in rows]


# --- Hybrid search --------------------------------------------------------------------

PER_ARM = 30


@dataclass(frozen=True)
class FusedHit:
    chunk_id: int
    document_id: int
    title: str
    source_uri: str
    heading_path: str
    text: str
    score: float  # the RRF score
    dense_rank: int | None  # position in the dense list, None if that arm did not return it
    fulltext_rank: int | None  # position in the full-text list, None if absent
    rerank_score: float | None = None  # set by the reranker: a raw logit, larger is better


def hybrid_search(
    engine: Engine,
    embedder: Embedder,
    question: str,
    group_ids: Sequence[int],
    *,
    per_arm: int = PER_ARM,
    limit: int = 20,
) -> list[FusedHit]:
    """Both arms apply the permission filter in their own SQL. Fusion only merges what they
    returned: it loads nothing by chunk id and so cannot add a chunk the user may not read."""
    dense = dense_search(engine, embedder.embed_query(question), group_ids, limit=per_arm)
    fulltext = fulltext_search(engine, question, group_ids, limit=per_arm)

    rows = {hit.chunk_id: hit for hit in [*dense, *fulltext]}
    dense_rank = {hit.chunk_id: rank for rank, hit in enumerate(dense, start=1)}
    fulltext_rank = {hit.chunk_id: rank for rank, hit in enumerate(fulltext, start=1)}
    fused = reciprocal_rank_fusion(
        [[hit.chunk_id for hit in dense], [hit.chunk_id for hit in fulltext]]
    )

    return [
        FusedHit(
            chunk_id=chunk_id,
            document_id=rows[chunk_id].document_id,
            title=rows[chunk_id].title,
            source_uri=rows[chunk_id].source_uri,
            heading_path=rows[chunk_id].heading_path,
            text=rows[chunk_id].text,
            score=score,
            dense_rank=dense_rank.get(chunk_id),
            fulltext_rank=fulltext_rank.get(chunk_id),
        )
        for chunk_id, score in fused[:limit]
    ]

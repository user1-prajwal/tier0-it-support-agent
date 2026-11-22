"""Store one document: version check, chunking, embedding, ACL and chunks in ONE transaction."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Connection, Engine, text

from app.db.vector import to_pgvector
from app.ingest.loader import CLASSIFICATION_GROUPS, DocumentError, parse_document
from app.retrieval.chunker import chunk_markdown
from app.retrieval.embedder import Embedder

INSERT_DOCUMENT = text(
    """
    INSERT INTO documents
        (title, source_uri, source_type, classification, content_hash, synthetic, license_note)
    VALUES
        (:title, :source_uri, :source_type, :classification, :content_hash, 
        :synthetic, :license_note)
    RETURNING id
    """
)

INSERT_CHUNK = text(
    """
    INSERT INTO chunks (document_id, ordinal, heading_path, text, token_count,
                        embedding, content_hash, embedding_model)
    VALUES (:document_id, :ordinal, :heading_path, :text, :token_count,
            CAST(:embedding AS vector), :content_hash, :embedding_model)
    """
)


class EmbeddingModelMismatch(RuntimeError):
    """The database holds vectors from a different model than the configured one."""


@dataclass(frozen=True)
class IngestResult:
    source_uri: str
    action: str  # "created", "updated" or "unchanged"
    chunks_written: int


def ingest_file(engine: Engine, path: Path, root: Path, embedder: Embedder) -> IngestResult:
    raw = path.read_bytes()
    document = parse_document(raw.decode("utf-8"))  # raises DocumentError on bad input
    source_uri = path.relative_to(root).as_posix()
    content_hash = hashlib.sha256(raw).hexdigest()

    with engine.begin() as conn:
        _refuse_mixed_models(conn, embedder.model_name)

        active = conn.execute(
            text(
                "SELECT id, content_hash FROM documents"
                " WHERE source_uri = :uri AND status = 'active' FOR UPDATE"
            ),
            {"uri": source_uri},
        ).one_or_none()
        if active is not None and active.content_hash == content_hash:
            return IngestResult(source_uri, "unchanged", 0)

        chunks = chunk_markdown(document.body)
        if not chunks:
            raise DocumentError("the document has no text below the front matter")
        vectors = embedder.embed_documents([chunk.embedding_text for chunk in chunks])

        if active is not None:
            conn.execute(
                text("UPDATE documents SET status = 'retired', retired_at = now() WHERE id = :id"),
                {"id": active.id},
            )

        document_id = conn.execute(
            INSERT_DOCUMENT,
            {
                "title": document.title,
                "source_uri": source_uri,
                "source_type": "markdown" if path.suffix.lower() == ".md" else "text",
                "classification": document.classification,
                "content_hash": content_hash,
                "synthetic": document.synthetic,
                "license_note": document.license_note,
            },
        ).scalar_one()

        _insert_acl(conn, document_id, CLASSIFICATION_GROUPS[document.classification])

        conn.execute(
            INSERT_CHUNK,
            [
                {
                    "document_id": document_id,
                    "ordinal": chunk.ordinal,
                    "heading_path": chunk.heading_path,
                    "text": chunk.text,
                    "token_count": max(1, len(chunk.text) // 4),  # rough estimate, ~4 chars/token
                    "embedding": to_pgvector(vector),
                    "content_hash": hashlib.sha256(chunk.text.encode()).hexdigest(),
                    "embedding_model": embedder.model_name,
                }
                for chunk, vector in zip(chunks, vectors, strict=True)
            ],
        )

    return IngestResult(source_uri, "created" if active is None else "updated", len(chunks))


def _refuse_mixed_models(conn: Connection, model_name: str) -> None:
    other = conn.execute(
        text("SELECT embedding_model FROM chunks WHERE embedding_model <> :model LIMIT 1"),
        {"model": model_name},
    ).scalar_one_or_none()
    if other is not None:
        raise EmbeddingModelMismatch(
            f"the database holds vectors from '{other}' but the configured model is "
            f"'{model_name}'. Mixing models makes search meaningless. Nothing was changed. "
            "Re-embedding is not built yet: use a fresh database."
        )


def _insert_acl(conn: Connection, document_id: int, group_names: list[str]) -> None:
    result = conn.execute(
        text(
            "INSERT INTO document_acl (document_id, group_id)"
            " SELECT CAST(:doc AS bigint), id FROM groups WHERE name = ANY(:names)"
        ),
        {"doc": document_id, "names": group_names},
    )
    if result.rowcount != len(group_names):  # a document with no ACL is invisible to everyone
        raise RuntimeError(f"expected {len(group_names)} ACL rows, wrote {result.rowcount}")
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

INSERT_DOC = text(
    """
    INSERT INTO documents
        (title, source_uri, source_type, classification, content_hash, status, synthetic)
    VALUES
        ('t', :uri, 'markdown', 'internal', :hash, :status, true)
    RETURNING id
    """
)


def test_only_one_active_version_per_source(engine):
    with engine.connect() as conn:
        outer = conn.begin()
        first = conn.execute(
            INSERT_DOC, {"uri": "kb/vpn.md", "hash": "h1", "status": "active"}
        ).scalar_one()

        # A second active version of the same source must be refused.
        with pytest.raises(IntegrityError), conn.begin_nested():
            conn.execute(INSERT_DOC, {"uri": "kb/vpn.md", "hash": "h2", "status": "active"})

        # Retiring the old version first makes room for the new one (the re-ingestion path).
        conn.execute(
            text("UPDATE documents SET status = 'retired', retired_at = now() WHERE id = :id"),
            {"id": first},
        )
        conn.execute(INSERT_DOC, {"uri": "kb/vpn.md", "hash": "h2", "status": "active"})

        outer.rollback()  # leave no rows behind
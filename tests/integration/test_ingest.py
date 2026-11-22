from pathlib import Path

import pytest
from sqlalchemy import text

from app.ingest.pipeline import EmbeddingModelMismatch, ingest_file
from app.retrieval.embedder import HashEmbedder

TEMPLATE = """\
+++
title = "Test document"
classification = "{classification}"
synthetic = true
+++
# Topic
## Section
{body}
"""

# Written out by hand on purpose: it must not share code with the mapping it checks.
EXPECTED_GROUPS = {
    "public": {"everyone"},
    "internal": {"everyone"},
    "it_restricted": {"helpdesk", "security"},
    "security_restricted": {"security"},
    "hr_confidential": {"hr"},
}


def write(root: Path, name: str, classification: str = "internal", body: str = "Some text."):
    path = root / name
    path.write_text(TEMPLATE.format(classification=classification, body=body))
    return path


def counts(engine) -> tuple[int, int, int]:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT count(*) FILTER (WHERE status = 'active'),"
                " count(*) FILTER (WHERE status = 'retired'),"
                " (SELECT count(*) FROM chunks) FROM documents"
            )
        ).one()
    return tuple(row)


def test_acl_follows_classification(engine, clean_db, tmp_path):
    for i, (classification, expected) in enumerate(EXPECTED_GROUPS.items()):
        path = write(tmp_path, f"doc{i}.md", classification=classification)
        ingest_file(engine, path, tmp_path, HashEmbedder())

        with engine.connect() as conn:
            groups = set(
                conn.execute(
                    text(
                        "SELECT g.name FROM document_acl a"
                        " JOIN documents d ON d.id = a.document_id"
                        " JOIN groups g ON g.id = a.group_id WHERE d.source_uri = :uri"
                    ),
                    {"uri": f"doc{i}.md"},
                ).scalars()
            )
        assert groups == expected, classification


def test_rerun_changes_nothing_and_an_edit_creates_a_new_version(engine, clean_db, tmp_path):
    path = write(tmp_path, "vpn.md", body="Original text.")

    first = ingest_file(engine, path, tmp_path, HashEmbedder())
    assert first.action == "created"
    assert counts(engine) == (1, 0, first.chunks_written)

    again = ingest_file(engine, path, tmp_path, HashEmbedder())
    assert again.action == "unchanged"
    assert counts(engine) == (1, 0, first.chunks_written)

    write(tmp_path, "vpn.md", body="Edited text.")
    edited = ingest_file(engine, path, tmp_path, HashEmbedder())
    assert edited.action == "updated"
    # One active version, one retired. Retired chunks stay for audit.
    assert counts(engine) == (1, 1, first.chunks_written + edited.chunks_written)


def test_refuses_to_mix_embedding_models(engine, clean_db, tmp_path):
    ingest_file(engine, write(tmp_path, "a.md"), tmp_path, HashEmbedder())

    class OtherModel(HashEmbedder):
        model_name = "some-other-model"

    with pytest.raises(EmbeddingModelMismatch):
        ingest_file(engine, write(tmp_path, "b.md"), tmp_path, OtherModel())
    assert counts(engine)[0] == 1
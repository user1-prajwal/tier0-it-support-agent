"""core schema: groups, documents, document_acl, chunks

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-21
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE groups (
            id   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            name text NOT NULL UNIQUE
        )
        """
    )
    # The four group names are part of the access model's vocabulary, not demo data.
    op.execute("INSERT INTO groups (name) VALUES ('everyone'), ('helpdesk'), ('security'), ('hr')")

    op.execute(
        """
        CREATE TABLE documents (
            id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            title          text NOT NULL,
            source_uri     text NOT NULL,
            source_type    text NOT NULL,
            classification text NOT NULL CHECK (classification IN (
                'public', 'internal', 'it_restricted', 'security_restricted', 'hr_confidential'
            )),
            content_hash   text NOT NULL,
            status         text NOT NULL DEFAULT 'active'
                               CHECK (status IN ('active', 'retired')),
            synthetic      boolean NOT NULL,
            license_note   text,
            created_at     timestamptz NOT NULL DEFAULT now(),
            retired_at     timestamptz
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX documents_one_active_per_source "
        "ON documents (source_uri) WHERE status = 'active'"
    )

    op.execute(
        """
        CREATE TABLE document_acl (
            document_id bigint NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
            group_id    bigint NOT NULL REFERENCES groups (id) ON DELETE CASCADE,
            PRIMARY KEY (document_id, group_id)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE chunks (
            id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            document_id     bigint NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
            ordinal         integer NOT NULL,
            heading_path    text NOT NULL,
            text            text NOT NULL,
            token_count     integer NOT NULL,
            embedding       vector(384) NOT NULL,
            tsv             tsvector GENERATED ALWAYS AS (
                                to_tsvector('english', heading_path || ' ' || text)
                            ) STORED,
            content_hash    text NOT NULL,
            embedding_model text NOT NULL,
            UNIQUE (document_id, ordinal)
        )
        """
    )
    op.execute("CREATE INDEX chunks_tsv_gin ON chunks USING gin (tsv)")


def downgrade() -> None:
    op.execute("DROP TABLE chunks")
    op.execute("DROP TABLE document_acl")
    op.execute("DROP TABLE documents")
    op.execute("DROP TABLE groups")
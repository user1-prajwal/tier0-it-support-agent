"""users, user_groups and documents.created_by

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-26
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE users (
            id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            email         text NOT NULL UNIQUE CHECK (email = lower(email)),
            display_name  text NOT NULL,
            password_hash text NOT NULL,
            role          text NOT NULL CHECK (role IN (
                              'employee', 'helpdesk', 'security_admin', 'hr'
                          )),
            is_active     boolean NOT NULL DEFAULT true,
            created_at    timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE user_groups (
            user_id  bigint NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            group_id bigint NOT NULL REFERENCES groups (id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, group_id)
        )
        """
    )
    # Nullable: the ingestion CLI has no logged-in user. The admin upload endpoint will set it.
    op.execute(
    "ALTER TABLE documents "
    "ADD COLUMN created_by bigint "
    "REFERENCES users (id) ON DELETE SET NULL"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE documents DROP COLUMN created_by")
    op.execute("DROP TABLE user_groups")
    op.execute("DROP TABLE users")
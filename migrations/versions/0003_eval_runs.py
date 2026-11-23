"""eval_runs: one row per recorded evaluation

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-23
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE eval_runs (
            id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            git_commit  text NOT NULL,
            split       text NOT NULL CHECK (split IN ('dev', 'test')),
            n_questions integer NOT NULL,
            config      jsonb NOT NULL,
            metrics     jsonb NOT NULL,
            started_at  timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE eval_runs")
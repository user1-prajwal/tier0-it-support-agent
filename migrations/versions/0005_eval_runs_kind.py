"""eval_runs: allow split = 'none' for runs that are not question-based

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-27
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE eval_runs DROP CONSTRAINT IF EXISTS eval_runs_split_check")
    op.execute(
        "ALTER TABLE eval_runs ADD CONSTRAINT eval_runs_split_check"
        " CHECK (split IN ('dev', 'test', 'none'))"
    )


def downgrade() -> None:
    # Rows with split = 'none' would violate the old rule, so they go with the downgrade.
    op.execute("DELETE FROM eval_runs WHERE split = 'none'")
    op.execute("ALTER TABLE eval_runs DROP CONSTRAINT IF EXISTS eval_runs_split_check")
    op.execute(
        "ALTER TABLE eval_runs ADD CONSTRAINT eval_runs_split_check"
        " CHECK (split IN ('dev', 'test'))"
    )
"""official_retention

Revision ID: 07abfea5f302
Revises: fcf037524f62
Create Date: 2026-09-21 15:26:56.982089
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '07abfea5f302'
down_revision: str | None = 'fcf037524f62'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for name in ("review_expires_at", "deletion_deadline_at", "cleanup_last_attempt_at", "deleted_at"):
        op.add_column("run_summaries", sa.Column(name, sa.DateTime(timezone=True), nullable=True))
    op.add_column("run_summaries", sa.Column("retention_state", sa.String(32), server_default="available", nullable=False))
    op.add_column("run_summaries", sa.Column("cleanup_reason", sa.String(32), nullable=True))
    op.add_column("run_summaries", sa.Column("cleanup_failure_category", sa.String(64), nullable=True))
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.execute(sa.text("UPDATE run_summaries SET review_expires_at = created_at + INTERVAL '23 hours', deletion_deadline_at = created_at + INTERVAL '24 hours' WHERE workflow_type = 'official'"))
    else:
        connection.execute(sa.text("UPDATE run_summaries SET review_expires_at = datetime(created_at, '+23 hours'), deletion_deadline_at = datetime(created_at, '+24 hours') WHERE workflow_type = 'official'"))


def downgrade() -> None:
    for name in ("cleanup_failure_category", "cleanup_reason", "retention_state", "deleted_at", "cleanup_last_attempt_at", "deletion_deadline_at", "review_expires_at"):
        op.drop_column("run_summaries", name)

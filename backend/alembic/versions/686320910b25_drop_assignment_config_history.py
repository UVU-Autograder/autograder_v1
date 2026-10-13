"""drop assignment config history

Revision ID: 686320910b25
Revises: dc32728b89fc
Create Date: 2026-10-13 14:58:20.990784
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '686320910b25'
down_revision: str | None = 'dc32728b89fc'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("assignment_config_history")


def downgrade() -> None:
    op.create_table(
        "assignment_config_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "assignment_id",
            sa.Integer(),
            sa.ForeignKey("assignments.id", name="fk_assignment_config_history_assignment", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

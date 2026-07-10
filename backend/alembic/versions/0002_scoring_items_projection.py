"""add scoring items projection

Revision ID: 0002_scoring_items_projection
Revises: 0001_initial_metadata
Create Date: 2026-06-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_scoring_items_projection"
down_revision: str | None = "0001_initial_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scoring_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("config_item_key", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("extra_credit", sa.Boolean(), nullable=False),
        sa.Column("item_type", sa.String(length=40), nullable=False),
        sa.Column("pytest_marker", sa.String(length=160), nullable=True),
        sa.Column("rubric_group_key", sa.String(length=120), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.UniqueConstraint("assignment_id", "config_item_key", name="uq_scoring_items_assignment_key"),
    )


def downgrade() -> None:
    op.drop_table("scoring_items")

"""drop scoring items projection

Revision ID: dc32728b89fc
Revises: a8cd706977f7
Create Date: 2026-10-13 14:27:47.901278
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'dc32728b89fc'
down_revision: str | None = 'a8cd706977f7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("scoring_items")


def downgrade() -> None:
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

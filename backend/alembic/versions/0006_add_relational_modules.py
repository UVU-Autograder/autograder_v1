"""add relational modules

Revision ID: 0006_add_relational_modules
Revises: 0005_db_improvements
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_add_relational_modules"
down_revision: str | None = "0005_db_improvements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create modules table
    op.create_table(
        "modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("concepts", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Add module_id to assignments in batch mode (for SQLite compatibility)
    with op.batch_alter_table("assignments") as batch_op:
        batch_op.add_column(sa.Column("module_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_assignments_module_id_modules",
            "modules",
            ["module_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    # 1. Drop module_id column from assignments in batch mode
    with op.batch_alter_table("assignments") as batch_op:
        batch_op.drop_constraint("fk_assignments_module_id_modules", type_="foreignkey")
        batch_op.drop_column("module_id")

    # 2. Drop modules table
    op.drop_table("modules")

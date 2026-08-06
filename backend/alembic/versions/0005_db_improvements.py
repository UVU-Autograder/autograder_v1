"""db improvements

Revision ID: 0005_db_improvements
Revises: 0004_remove_due_label
Create Date: 2026-06-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_db_improvements"
down_revision: str | None = "0004_remove_due_label"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Drop sections.name column
    with op.batch_alter_table("sections") as batch_op:
        batch_op.drop_column("name")

    # 2. Add courses.instructor_id and courses.ia_id columns
    with op.batch_alter_table("courses") as batch_op:
        batch_op.add_column(sa.Column("instructor_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_courses_instructor", ondelete="SET NULL"), nullable=True))
        batch_op.add_column(sa.Column("ia_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_courses_ia", ondelete="SET NULL"), nullable=True))

    # 3. Alter staff_access.section_id to be NOT NULL
    with op.batch_alter_table("staff_access") as batch_op:
        batch_op.alter_column("section_id", existing_type=sa.Integer(), nullable=False)

    # 4. Add assignment_configs.version column (non-nullable with default '1')
    with op.batch_alter_table("assignment_configs") as batch_op:
        batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    # 5. Create assignment_config_history table
    op.create_table(
        "assignment_config_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignments.id", name="fk_assignment_config_history_assignment", ondelete="CASCADE"), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    # 1. Drop assignment_config_history table
    op.drop_table("assignment_config_history")

    # 2. Drop assignment_configs.version column
    with op.batch_alter_table("assignment_configs") as batch_op:
        batch_op.drop_column("version")

    # 3. Alter staff_access.section_id to be nullable
    with op.batch_alter_table("staff_access") as batch_op:
        batch_op.alter_column("section_id", existing_type=sa.Integer(), nullable=True)

    # 4. Drop courses.instructor_id and courses.ia_id columns
    with op.batch_alter_table("courses") as batch_op:
        batch_op.drop_column("ia_id")
        batch_op.drop_column("instructor_id")

    # 5. Add sections.name column back
    with op.batch_alter_table("sections") as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(length=255), nullable=True))

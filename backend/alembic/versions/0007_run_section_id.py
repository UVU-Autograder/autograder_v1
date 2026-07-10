"""add section_id to run_summaries

Revision ID: 0007_run_section_id
Revises: 0006_add_relational_modules
Create Date: 2026-07-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_run_section_id"
down_revision: str | None = "0006_add_relational_modules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("run_summaries") as batch_op:
        batch_op.add_column(sa.Column("section_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_run_summaries_section_id_sections",
            "sections",
            ["section_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Backfill official runs: first active section of the assignment's course.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE run_summaries
            SET section_id = (
                SELECT s.id FROM sections s
                JOIN assignments a ON a.course_id = s.course_id
                WHERE a.id = run_summaries.assignment_id
                  AND s.is_active
                ORDER BY s.id
                LIMIT 1
            )
            WHERE workflow_type = 'official' AND section_id IS NULL
            """
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("run_summaries") as batch_op:
        batch_op.drop_constraint(
            "fk_run_summaries_section_id_sections", type_="foreignkey"
        )
        batch_op.drop_column("section_id")

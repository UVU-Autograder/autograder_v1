"""Add azure_oid to users and make staff_access.course_id nullable.

Revision ID: b73c4d5e6f10
Revises: a82bd9410e21
Create Date: 2026-09-23 15:47:00
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b73c4d5e6f10"
down_revision: str | None = "a82bd9410e21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("azure_oid", sa.String(length=64), nullable=True))
    op.create_index("ix_users_azure_oid", "users", ["azure_oid"], unique=True)

    with op.batch_alter_table("staff_access") as batch_op:
        batch_op.alter_column("course_id", existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column("section_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("staff_access") as batch_op:
        batch_op.alter_column("section_id", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("course_id", existing_type=sa.Integer(), nullable=False)

    op.drop_index("ix_users_azure_oid", table_name="users")
    op.drop_column("users", "azure_oid")

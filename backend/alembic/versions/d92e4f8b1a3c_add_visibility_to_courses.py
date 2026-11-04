"""Add visibility column to courses table.

Revision ID: d92e4f8b1a3c
Revises: c83a1f9e2b4d
"""
from alembic import op
import sqlalchemy as sa

revision = "d92e4f8b1a3c"
down_revision = "c83a1f9e2b4d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("courses") as batch_op:
        batch_op.add_column(
            sa.Column(
                "visibility",
                sa.String(length=40),
                nullable=False,
                server_default="everyone",
            )
        )


def downgrade():
    with op.batch_alter_table("courses") as batch_op:
        batch_op.drop_column("visibility")

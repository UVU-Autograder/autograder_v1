"""Add use_allowed_concepts column to courses table.

Revision ID: c83a1f9e2b4d
Revises: e7b91d2c3f4a
"""
from alembic import op
import sqlalchemy as sa

revision = "c83a1f9e2b4d"
down_revision = "e7b91d2c3f4a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("courses") as batch_op:
        batch_op.add_column(
            sa.Column(
                "use_allowed_concepts",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            )
        )


def downgrade():
    with op.batch_alter_table("courses") as batch_op:
        batch_op.drop_column("use_allowed_concepts")

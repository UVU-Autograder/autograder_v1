"""Persist server-managed reference inventories.

Revision ID: 9c72df410a23
Revises: 686320910b25
"""
from alembic import op
import sqlalchemy as sa

revision = "9c72df410a23"
down_revision = "686320910b25"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assignment_configs", sa.Column("validated_test_manifest", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("assignment_configs", "validated_test_manifest")

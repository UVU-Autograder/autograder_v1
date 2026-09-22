"""remove due label

Revision ID: 0004_remove_due_label
Revises: 0003_drop_test_cases
Create Date: 2026-06-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_remove_due_label"
down_revision: str | None = "0003_drop_test_cases"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("assignments") as batch_op:
        batch_op.drop_column("due_label")


def downgrade() -> None:
    with op.batch_alter_table("assignments") as batch_op:
        batch_op.add_column(sa.Column("due_label", sa.String(length=120), nullable=True))

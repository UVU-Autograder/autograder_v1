"""rename_config_json_to_config

Revision ID: a8cd706977f7
Revises: 4de4fdb067c3
Create Date: 2026-10-06 11:50:07.758146
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'a8cd706977f7'
down_revision: str | None = '4de4fdb067c3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("assignment_configs") as batch_op:
        batch_op.alter_column("config_json", new_column_name="config")
    with op.batch_alter_table("assignment_config_history") as batch_op:
        batch_op.alter_column("config_json", new_column_name="config")


def downgrade() -> None:
    with op.batch_alter_table("assignment_config_history") as batch_op:
        batch_op.alter_column("config", new_column_name="config_json")
    with op.batch_alter_table("assignment_configs") as batch_op:
        batch_op.alter_column("config", new_column_name="config_json")

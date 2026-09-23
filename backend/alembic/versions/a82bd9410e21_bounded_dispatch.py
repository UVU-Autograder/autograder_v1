"""Durable execution reservations and official dispatch outbox."""
from alembic import op
import sqlalchemy as sa

revision = "a82bd9410e21"
down_revision = "07abfea5f302"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("run_summaries", sa.Column("export_packaging_seconds", sa.Float(), nullable=True))
    op.create_table("execution_tickets",
        sa.Column("owner", sa.String(100), primary_key=True),
        sa.Column("token", sa.String(36), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_execution_tickets_state", "execution_tickets", ["state"])
    op.create_table("official_dispatches",
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("run_summaries.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("ready", sa.Boolean(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False))


def downgrade():
    op.drop_table("official_dispatches")
    op.drop_table("execution_tickets")
    op.drop_column("run_summaries", "export_packaging_seconds")

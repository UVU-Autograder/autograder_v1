"""Create audit_records table for structured audit logging and FERPA compliance.

Revision ID: e7b91d2c3f4a
Revises: 9c72df410a23
"""
from alembic import op
import sqlalchemy as sa

revision = "e7b91d2c3f4a"
down_revision = "9c72df410a23"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event", sa.String(length=100), nullable=False),
        sa.Column("workflow_type", sa.String(length=50), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("course_id", sa.String(length=50), nullable=True),
        sa.Column("assignment_id", sa.String(length=100), nullable=True),
        sa.Column("run_id", sa.Integer(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_audit_records_timestamp", "audit_records", ["timestamp"])
    op.create_index("ix_audit_records_event", "audit_records", ["event"])
    op.create_index("ix_audit_records_workflow_type", "audit_records", ["workflow_type"])
    op.create_index("ix_audit_records_actor_user_id", "audit_records", ["actor_user_id"])
    op.create_index("ix_audit_records_course_id", "audit_records", ["course_id"])
    op.create_index("ix_audit_records_run_id", "audit_records", ["run_id"])
    op.create_index(
        "ix_audit_records_event_timestamp",
        "audit_records",
        ["event", "timestamp"],
    )


def downgrade():
    op.drop_index("ix_audit_records_event_timestamp", table_name="audit_records")
    op.drop_index("ix_audit_records_run_id", table_name="audit_records")
    op.drop_index("ix_audit_records_course_id", table_name="audit_records")
    op.drop_index("ix_audit_records_actor_user_id", table_name="audit_records")
    op.drop_index("ix_audit_records_workflow_type", table_name="audit_records")
    op.drop_index("ix_audit_records_event", table_name="audit_records")
    op.drop_index("ix_audit_records_timestamp", table_name="audit_records")
    op.drop_table("audit_records")

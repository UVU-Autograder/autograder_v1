from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.domains.assignments.models import Assignment


class RunSummary(Base):
    __tablename__ = "run_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_type: Mapped[str] = mapped_column(String(40))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    sandbox_session_hash: Mapped[str | None] = mapped_column(String(255))
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"))
    section_id: Mapped[int | None] = mapped_column(
        ForeignKey("sections.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(40))
    total_submission_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    timeout_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    token_usage_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    review_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deletion_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retention_state: Mapped[str] = mapped_column(String(32), default="available", server_default="available")
    cleanup_reason: Mapped[str | None] = mapped_column(String(32))
    cleanup_last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cleanup_failure_category: Mapped[str | None] = mapped_column(String(64))

    assignment: Mapped["Assignment"] = relationship(back_populates="run_summaries")


@event.listens_for(RunSummary, "before_insert")
def initialize_retention(mapper, connection, target: RunSummary) -> None:
    if target.workflow_type == "official":
        target.created_at = target.created_at or datetime.now(UTC)
        target.review_expires_at = target.created_at + timedelta(hours=23)
        target.deletion_deadline_at = target.created_at + timedelta(hours=24)

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditRecord(Base):
    """Structured audit trail record for FERPA and security compliance."""

    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    event: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    workflow_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    course_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    assignment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    run_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_audit_records_event_timestamp", "event", "timestamp"),
    )

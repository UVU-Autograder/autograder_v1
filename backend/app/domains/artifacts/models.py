from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssignmentArtifact(Base):
    __tablename__ = "assignment_artifacts"
    __table_args__ = (UniqueConstraint("assignment_id", "artifact_key", name="uq_assignment_artifacts_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"))
    artifact_key: Mapped[str] = mapped_column(String(120))
    artifact_type: Mapped[str] = mapped_column(String(40))
    storage_ref: Mapped[str | None] = mapped_column(String(500))
    display_filename: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(120))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assignment: Mapped["Assignment"] = relationship(back_populates="artifacts")

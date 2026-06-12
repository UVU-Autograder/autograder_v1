from datetime import datetime
import os
from pathlib import Path

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func, event
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


@event.listens_for(AssignmentArtifact, "after_delete")
def delete_physical_file(mapper, connection, target) -> None:
    """Clean up file from local storage when AssignmentArtifact record is deleted."""
    if target.storage_ref:
        ref = target.storage_ref
        file_path = None
        if ref.startswith("file://"):
            # Strip file:// prefix
            # On Windows, need to handle file:///C:/path (3 slashes) or file://C:/path (2 slashes)
            clean_ref = ref[7:]
            if clean_ref.startswith("/"):
                clean_ref = clean_ref[1:]
            file_path = Path(clean_ref).resolve()
        elif ref.startswith("/") or ref.startswith("\\") or (len(ref) > 1 and ref[1] == ":"):
            # Handle absolute paths directly, ignoring seed:// or relative stubs
            if not ref.startswith("seed://"):
                file_path = Path(ref).resolve()

        if file_path and file_path.exists() and file_path.is_file():
            try:
                os.remove(file_path)
            except Exception:
                pass

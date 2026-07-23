from datetime import datetime
import os
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, event, func
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.domains.courses.models import Course, Module
    from app.domains.runs.models import RunSummary


import logging

logger = logging.getLogger(__name__)

def file_storage_ref_to_path(storage_ref: str) -> Path | None:

    if not storage_ref.startswith("file://"):
        return None
    return Path(storage_ref[len("file://"):]).resolve()


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
            file_path = file_storage_ref_to_path(ref)
        elif ref.startswith("/") or ref.startswith("\\") or (len(ref) > 1 and ref[1] == ":"):
            if not ref.startswith("seed://"):
                file_path = Path(ref).resolve()

        if file_path and file_path.exists() and file_path.is_file():
            try:
                os.remove(file_path)
            except Exception as exc:
                logger.warning("Failed to remove physical artifact file %s: %s", file_path, exc)



class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (UniqueConstraint("course_id", "slug", name="uq_assignments_course_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    slug: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(40), default="python")
    canvas_ref: Mapped[str | None] = mapped_column(String(255))
    sandbox_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    module_id: Mapped[int | None] = mapped_column(ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)

    course: Mapped["Course"] = relationship(back_populates="assignments")
    module: Mapped["Module | None"] = relationship(back_populates="assignments")
    config: Mapped["AssignmentConfig | None"] = relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
        uselist=False,
    )
    artifacts: Mapped[list["AssignmentArtifact"]] = relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
    )
    scoring_items: Mapped[list["ScoringItem"]] = relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="ScoringItem.display_order",
    )
    run_summaries: Mapped[list["RunSummary"]] = relationship(back_populates="assignment")


class AssignmentConfig(Base):
    __tablename__ = "assignment_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
        unique=True,
    )
    config_json: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    assignment: Mapped[Assignment] = relationship(back_populates="config")


class AssignmentConfigHistory(Base):
    __tablename__ = "assignment_config_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"))
    config_json: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())







class ScoringItem(Base):
    __tablename__ = "scoring_items"
    __table_args__ = (UniqueConstraint("assignment_id", "config_item_key", name="uq_scoring_items_assignment_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"))
    config_item_key: Mapped[str] = mapped_column(String(120))
    label: Mapped[str] = mapped_column(String(255))
    points: Mapped[int] = mapped_column(Integer)
    extra_credit: Mapped[bool] = mapped_column(Boolean, default=False)
    item_type: Mapped[str] = mapped_column(String(40))
    pytest_marker: Mapped[str | None] = mapped_column(String(160))
    rubric_group_key: Mapped[str | None] = mapped_column(String(120))
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    assignment: Mapped[Assignment] = relationship(back_populates="scoring_items")

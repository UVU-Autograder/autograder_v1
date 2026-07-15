from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.domains.courses.models import Course, Module
    from app.domains.artifacts.models import AssignmentArtifact
    from app.domains.runs.models import RunSummary


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

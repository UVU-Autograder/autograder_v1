from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    term: Mapped[str] = mapped_column(String(80))
    default_concepts: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    instructor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ia_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sections: Mapped[list["Section"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    staff_access: Mapped[list["StaffAccess"]] = relationship(back_populates="course")
    instructor: Mapped["User | None"] = relationship(foreign_keys=[instructor_id], back_populates="instructed_courses")
    ia: Mapped["User | None"] = relationship(foreign_keys=[ia_id], back_populates="ia_courses")


class Section(Base):
    __tablename__ = "sections"
    __table_args__ = (UniqueConstraint("course_id", "crn", name="uq_sections_course_crn"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    crn: Mapped[str] = mapped_column(String(40))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    course: Mapped[Course] = relationship(back_populates="sections")
    staff_access: Mapped[list["StaffAccess"]] = relationship(back_populates="section")

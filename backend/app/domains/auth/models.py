from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    staff_access: Mapped[list["StaffAccess"]] = relationship(back_populates="user")
    instructed_courses: Mapped[list["Course"]] = relationship(
        foreign_keys="Course.instructor_id",
        back_populates="instructor",
    )
    ia_courses: Mapped[list["Course"]] = relationship(
        foreign_keys="Course.ia_id",
        back_populates="ia",
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)

    staff_access: Mapped[list["StaffAccess"]] = relationship(back_populates="role")


class StaffAccess(Base):
    __tablename__ = "staff_access"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "course_id", "section_id", name="uq_staff_access_scope"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship(back_populates="staff_access")
    role: Mapped[Role] = relationship(back_populates="staff_access")
    course: Mapped["Course"] = relationship(back_populates="staff_access")
    section: Mapped["Section"] = relationship(back_populates="staff_access")

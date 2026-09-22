from typing import Annotated

from fastapi import Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth_utils import decode_access_token
from app.db.session import get_db
from app.domains.auth.models import User

DbSession = Annotated[Session, Depends(get_db)]

security = HTTPBearer(auto_error=False)


def get_current_user(
    db: DbSession,
    response: Response,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ] = None,
) -> User:
    """Retrieve current authenticated user from JWT token.

    Auto-provisions the user in the database on first login.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    email = payload["email"]
    name = payload.get("name")

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.domains.auth.models import StaffAccess

    user = db.scalar(
        select(User)
        .options(selectinload(User.staff_access).selectinload(StaffAccess.role))
        .where(User.email == email)
    )

    if user is None:
        user = User(email=email, display_name=name, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive.",
        )

    # Generate new token with sliding expiration
    from app.core.auth_utils import create_access_token
    refreshed_token = create_access_token(email=email, display_name=name)
    response.headers["x-refresh-token"] = refreshed_token

    return user


def get_optional_user(
    db: DbSession,
    response: Response,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ] = None,
) -> User | None:
    """Return the authenticated user when a valid Bearer token is present, else None."""
    if not credentials:
        return None
    try:
        return get_current_user(db, response, credentials)
    except HTTPException:
        return None

def require_role(allowed_roles: list[str]):
    """Standardized guard to enforce specific user roles."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        user_roles = {
            access.role.name
            for access in user.staff_access
            if access.is_active and access.role is not None
        }
        if not user_roles.intersection(allowed_roles) and not any(
            r == "admin" for r in user_roles
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for user role.",
            )
        return user

    return dependency


def require_staff(user: User = Depends(get_current_user)) -> User:
    """Enforces that the user is a staff member (admin, instructor, or IA)."""

    user_roles = {
        access.role.name
        for access in user.staff_access
        if access.is_active and access.role is not None
    }
    if not user_roles.intersection({"admin", "instructor", "IA"}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required.",
        )
    return user


def user_is_admin(user: User) -> bool:
    return any(
        access.is_active and access.role is not None and access.role.name == "admin"
        for access in user.staff_access
    )



def assert_course_section_access(
    db: Session,
    user: User,
    *,
    course_code: str,
    section_id: int,
) -> None:
    """Require admin or active StaffAccess for course_code + section_id."""
    if user_is_admin(user):
        return

    from sqlalchemy import select

    from app.domains.courses.models import Course, Section

    course = db.scalar(select(Course).where(Course.code == course_code))
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    section = db.scalar(
        select(Section).where(
            Section.id == section_id,
            Section.course_id == course.id,
            Section.is_active.is_(True),
        )
    )
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found for this course.",
        )

    has_grant = any(
        access.is_active
        and access.course_id == course.id
        and access.section_id == section_id
        and access.role.name in {"admin", "instructor", "IA"}
        for access in user.staff_access
    )
    if not has_grant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No staff access for this course section.",
        )


def accessible_section_ids_for_course(db: Session, user: User, course_code: str) -> list[int] | None:
    """Return section IDs the user may access, or None if admin (all sections)."""
    from sqlalchemy import select

    from app.domains.courses.models import Course

    course = db.scalar(select(Course).where(Course.code == course_code))
    if course is None:
        return []

    if user_is_admin(user):
        return None  # all sections

    return [
        access.section_id
        for access in user.staff_access
        if access.is_active
        and access.course_id == course.id
        and access.role.name in {"admin", "instructor", "IA"}
    ]


def assert_run_section_access(
    db: Session,
    user: User,
    *,
    course_code: str,
    section_id: int | None,
) -> None:
    """Enforce section grants for an official run. Legacy null section_id = admin only."""
    if section_id is None:
        if not user_is_admin(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Legacy run without section; admin access required.",
            )
        return
    assert_course_section_access(
        db, user, course_code=course_code, section_id=section_id
    )

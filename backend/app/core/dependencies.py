from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.auth.models import User

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession) -> User:
    """Retrieve current authenticated user.

    Stubbed to return the seeded development staff user for M1.
    """
    from sqlalchemy import select
    user = db.scalar(select(User).where(User.email == "dev.staff@uvu.edu"))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    return user


def require_role(allowed_roles: list[str]):
    """Standardized guard to enforce specific user roles."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        user_roles = {access.role.name for access in user.staff_access if access.is_active}
        if not user_roles.intersection(allowed_roles) and not any(r == "admin" for r in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for user role.",
            )
        return user
    return dependency


def require_staff(user: User = Depends(get_current_user)) -> User:
    """Enforces that the user is a staff member (admin, instructor, or IA)."""

    user_roles = {access.role.name for access in user.staff_access if access.is_active}
    if not user_roles.intersection({"admin", "instructor", "IA"}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required.",
        )
    return user

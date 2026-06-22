from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.auth.models import User

DbSession = Annotated[Session, Depends(get_db)]


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.auth_utils import decode_access_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None
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
    user = db.scalar(select(User).where(User.email == email))
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

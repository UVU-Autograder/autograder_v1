from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.auth_utils import create_access_token
from app.core.dependencies import DbSession, get_current_user
from app.core.settings import get_settings
from app.domains.auth.models import StaffAccess, User

router = APIRouter()


class MockLoginRequest(BaseModel):
    email: str
    display_name: str | None = None


def _active_role_names(user: User) -> list[str]:
    roles = sorted(
        {
            access.role.name
            for access in user.staff_access
            if access.is_active and access.role is not None
        }
    )
    return roles


@router.post("/mock-login")
def mock_login(request: MockLoginRequest, db: DbSession):
    """Local mock login endpoint. Enabled only in SQLite local development mode.

    Generates a signed JWT token. Auto-provisions the user if they do not exist.
    """
    settings = get_settings()
    if not settings.is_sqlite and settings.enable_mock_login is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock login is only available in local development mode or when explicitly enabled.",
        )

    email = request.email.strip().lower()
    if not email.endswith("@uvu.edu"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mock login is restricted to @uvu.edu email addresses.",
        )

    user = db.scalar(
        select(User)
        .options(selectinload(User.staff_access).selectinload(StaffAccess.role))
        .where(User.email == email)
    )
    if user is None:
        user = User(email=email, display_name=request.display_name, is_active=True)
        db.add(user)
        db.commit()
        user = db.scalar(
            select(User)
            .options(selectinload(User.staff_access).selectinload(StaffAccess.role))
            .where(User.email == email)
        )
        assert user is not None

    token = create_access_token(email=email, display_name=user.display_name)

    return {
        "access_token": token,
        "token_type": "bearer",
        "email": user.email,
        "display_name": user.display_name,
        "roles": _active_role_names(user),
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated staff user's profile and active role names."""
    return {
        "email": current_user.email,
        "display_name": current_user.display_name,
        "roles": _active_role_names(current_user),
    }

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.auth_utils import create_access_token
from app.core.dependencies import DbSession, get_current_user
from app.core.settings import get_settings
from app.domains.auth.models import StaffAccess, User
from app.integrations.auth.microsoft import verify_microsoft_id_token

router = APIRouter()


class MockLoginRequest(BaseModel):
    email: str
    display_name: str | None = None


class MicrosoftLoginRequest(BaseModel):
    id_token: str


def _active_role_names(user: User) -> list[str]:
    roles = sorted(
        {
            access.role.name
            for access in user.staff_access
            if access.is_active and access.role is not None
        }
    )
    return roles


@router.post("/microsoft-login")
def microsoft_login(request: MicrosoftLoginRequest, db: DbSession):
    """Institutional Microsoft sign-in endpoint.

    Verifies the RS256 Microsoft ID token against Microsoft's public JWKS.
    Enforces that the email has an @uvu.edu domain, matches an existing User record,
    and has active StaffAccess. Unauthorized accounts are rejected with 403 Forbidden.
    """
    claims = verify_microsoft_id_token(request.id_token)
    email = claims.email

    user = db.scalar(
        select(User)
        .options(selectinload(User.staff_access).selectinload(StaffAccess.role))
        .where(User.email == email)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending staff authorization. Please contact an administrator to request staff access.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    active_roles = _active_role_names(user)
    if not active_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active staff roles assigned. Please contact an administrator to request staff access.",
        )

    # Bind azure_oid if not already set, and reject conflicting identity mismatch
    updated = False
    if claims.azure_oid:
        if user.azure_oid is None:
            user.azure_oid = claims.azure_oid
            updated = True
        elif user.azure_oid != claims.azure_oid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Institutional Microsoft identity mismatch with existing staff profile.",
            )
    if claims.display_name and not user.display_name:
        user.display_name = claims.display_name
        updated = True
    if updated:
        db.commit()

    token = create_access_token(email=email, display_name=user.display_name, user_id=user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "email": user.email,
        "display_name": user.display_name,
        "roles": active_roles,
    }


@router.post("/mock-login")
def mock_login(request: MockLoginRequest, db: DbSession):
    """Local mock login endpoint. Enabled only in SQLite local development mode.

    Generates a signed JWT token. Auto-provisions the user if they do not exist.
    """
    settings = get_settings()
    if not settings.mock_login_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock login is disabled. Production staff authentication requires Microsoft Entra ID.",
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

    token = create_access_token(email=email, display_name=user.display_name, user_id=user.id)

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

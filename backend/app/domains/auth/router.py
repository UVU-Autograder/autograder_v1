from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.core.auth_utils import create_access_token
from app.core.dependencies import DbSession
from app.core.settings import get_settings
from app.domains.auth.models import User

router = APIRouter()

class MockLoginRequest(BaseModel):
    email: str
    display_name: str | None = None

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

    # Check/auto-provision user
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, display_name=request.display_name, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(email=email, display_name=user.display_name)

    return {
        "access_token": token,
        "token_type": "bearer",
        "email": user.email,
        "display_name": user.display_name,
    }

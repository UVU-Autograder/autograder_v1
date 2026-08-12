from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status

from app.core.settings import get_settings


def create_access_token(email: str, display_name: str | None = None) -> str:
    """Create a signed JWT token for the user."""
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expiration_minutes)

    payload = {
        "email": email.strip().lower(),
        "name": display_name,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.
    
    Raises HTTPException (401) on invalid signature, expiration, or email constraints.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        email: str | None = payload.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing user email.",
            )

        # Enforce @uvu.edu domain constraint
        if not email.lower().endswith("@uvu.edu"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access restricted to @uvu.edu domains.",
            )

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

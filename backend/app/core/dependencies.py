from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

DbSession = Annotated[Session, Depends(get_db)]


def require_stubbed_staff() -> dict[str, str]:
    """Temporary staff dependency until Microsoft OAuth is wired."""

    return {"email": "dev.staff@uvu.edu", "role": "admin"}

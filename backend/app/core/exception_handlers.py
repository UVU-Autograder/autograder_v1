from __future__ import annotations

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.audit_log import audit_access_denied


class AppError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Centralized handler intercepting 401/403 denials and emitting audit records."""
    if exc.status_code in (401, 403):
        actor_user_id = getattr(request.state, "actor_user_id", None)
        if actor_user_id is None:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                raw_token = auth_header[7:].strip()
                try:
                    unverified = jwt.decode(raw_token, options={"verify_signature": False})
                    candidate = unverified.get("user_id") or unverified.get("sub")
                    if isinstance(candidate, int):
                        actor_user_id = candidate
                    elif isinstance(candidate, str) and candidate.isdigit():
                        actor_user_id = int(candidate)
                except Exception:
                    actor_user_id = None

        audit_access_denied(
            status_code=exc.status_code,
            reason=str(exc.detail),
            actor_user_id=actor_user_id,
            request=request,
        )

    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )

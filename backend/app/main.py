import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint

from app.api.router import api_router
from app.core.audit_log import configure_audit_logging
from app.core.exception_handlers import AppError, app_error_handler, http_exception_handler
from app.core.settings import get_settings
from app.db.seed import initialize_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_audit_logging()
    settings = get_settings()
    settings.validate_production_security()
    if settings.is_sqlite:
        initialize_database(seed=True)
    yield

def create_app() -> FastAPI:
    settings = get_settings()
    settings.validate_production_security()
    app = FastAPI(title="Autograder API", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(
        AppError,
        cast(
            Callable[[Request, Exception], JSONResponse],
            app_error_handler,
        ),
    )
    app.add_exception_handler(
        StarletteHTTPException,
        cast(
            Callable[[Request, Exception], JSONResponse],
            http_exception_handler,
        ),
    )
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.parsed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-refresh-token"],
    )
    @app.middleware("http")
    async def private_cache_control(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        path = request.url.path
        if path.startswith(("/staff/", "/runs/", "/sandbox/runs/", "/auth/")):
            response.headers["Cache-Control"] = "no-store"
        return response

    app.include_router(api_router)

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})[
            "BearerAuth"
        ] = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
    return app

app = create_app()

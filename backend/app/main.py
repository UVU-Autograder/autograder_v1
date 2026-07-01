from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.router import api_router
from app.core.exception_handlers import AppError, app_error_handler
from app.core.settings import get_settings
from app.db.seed import initialize_database


import asyncio
import logging

logger = logging.getLogger(__name__)


async def schedule_workspaces_cleanup():
    # Wait 10 seconds after startup before the first run
    await asyncio.sleep(10)
    while True:
        try:
            from app.domains.runs.tasks import cleanup_expired_workspaces
            cleanup_expired_workspaces()
        except Exception as e:
            logger.error("Error in background workspace cleanup: %s", e)
        # Run every hour
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.is_sqlite:
        initialize_database(seed=True)

    cleanup_task = asyncio.create_task(schedule_workspaces_cleanup())
    try:
        yield
    finally:
        cleanup_task.cancel()



def create_app() -> FastAPI:
    app = FastAPI(title="Autograder API", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            # DEV ONLY: Allow Vercel deployments for Tailscale Funnel testing
            "https://*.vercel.app", 
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-refresh-token"],
    )
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

    app.openapi = custom_openapi
    return app


app = create_app()

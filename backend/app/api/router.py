from fastapi import APIRouter

from app.domains.assignments.router import router as assignments_router
from app.domains.courses.router import router as courses_router
from app.domains.ingestion.router import router as ingestion_router
from app.domains.runs.router import router as runs_router, staff_runs_router
from app.domains.sandbox.router import router as sandbox_router

from app.api.health import router as health_router
from app.domains.auth.router import router as auth_router
from app.domains.auth.admin_router import router as admin_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(admin_router)
api_router.include_router(sandbox_router)
api_router.include_router(runs_router)
api_router.include_router(staff_runs_router)
api_router.include_router(courses_router)
api_router.include_router(assignments_router)
api_router.include_router(ingestion_router)


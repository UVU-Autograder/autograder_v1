from fastapi import APIRouter

from app.domains.runs.router import router as runs_router
from app.domains.sandbox.router import router as sandbox_router

api_router = APIRouter()
api_router.include_router(sandbox_router)
api_router.include_router(runs_router)

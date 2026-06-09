from fastapi import APIRouter, HTTPException

from app.domains.runs.schemas import RunStatusResponse
from app.domains.sandbox.service import sandbox_service

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}/status", response_model=RunStatusResponse)
def get_run_status(run_id: str) -> RunStatusResponse:
    status = sandbox_service.get_status(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return status

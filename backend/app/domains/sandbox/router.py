from fastapi import APIRouter, File, Header, HTTPException, Response, UploadFile

from app.core.dependencies import DbSession
from app.domains.sandbox.catalog import (
    get_sandbox_assignment,
    list_sandbox_assignments,
    list_sandbox_courses,
)
from app.domains.sandbox.schemas import (
    SandboxAssignmentDetail,
    SandboxAssignmentListResponse,
    SandboxCancelResponse,
    SandboxCourseListResponse,
    SandboxRunCreateResponse,
    SandboxRunResultResponse,
)
from app.domains.sandbox.service import sandbox_service

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


@router.get("/courses", response_model=SandboxCourseListResponse)
def list_courses(db: DbSession) -> SandboxCourseListResponse:
    return list_sandbox_courses(db)


@router.get(
    "/courses/{course_id}/assignments",
    response_model=SandboxAssignmentListResponse,
)
def list_assignments(
    db: DbSession,
    course_id: str,
    x_sandbox_session: str | None = Header(default=None),
) -> SandboxAssignmentListResponse:
    assignments = list_sandbox_assignments(
        db,
        course_id,
        sandbox_service.quota_for_session(x_sandbox_session),
    )
    if assignments is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return assignments


@router.get(
    "/courses/{course_id}/assignments/{assignment_id}",
    response_model=SandboxAssignmentDetail,
)
def get_assignment(
    db: DbSession,
    course_id: str,
    assignment_id: str,
    x_sandbox_session: str | None = Header(default=None),
) -> SandboxAssignmentDetail:
    assignment = get_sandbox_assignment(
        db,
        course_id,
        assignment_id,
        sandbox_service.quota_for_session(x_sandbox_session),
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    return assignment


@router.post(
    "/courses/{course_id}/assignments/{assignment_id}/runs",
    response_model=SandboxRunCreateResponse,
    status_code=202,
)
async def create_run(
    db: DbSession,
    response: Response,
    course_id: str,
    assignment_id: str,
    bundle: UploadFile = File(...),
    x_sandbox_session: str | None = Header(default=None),
) -> SandboxRunCreateResponse:
    await bundle.close()
    assignment = get_sandbox_assignment(
        db,
        course_id,
        assignment_id,
        sandbox_service.quota_for_session(x_sandbox_session),
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    run, session, error_status = sandbox_service.create_run(
        course_id=course_id,
        assignment_id=assignment_id,
        session_id=x_sandbox_session,
        assignment_exists=True,
        max_score=assignment.max_score,
    )
    response.headers["X-Sandbox-Session"] = session
    if error_status == 429:
        raise HTTPException(status_code=429, detail="Sandbox upload quota exhausted.")
    if error_status == 503:
        raise HTTPException(
            status_code=503,
            detail="Sandbox queue is full. Please retry after capacity clears.",
        )
    return run


@router.post("/runs/{run_id}/cancel", response_model=SandboxCancelResponse)
def cancel_run(
    run_id: str,
    x_sandbox_session: str | None = Header(default=None),
) -> SandboxCancelResponse:
    cancelled = sandbox_service.cancel_run(run_id, x_sandbox_session)
    if cancelled is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    if cancelled == "not_cancelable":
        raise HTTPException(status_code=409, detail="Only queued sandbox runs can be cancelled.")
    return cancelled


@router.get("/runs/{run_id}/result", response_model=SandboxRunResultResponse)
def get_result(
    run_id: str,
    x_sandbox_session: str | None = Header(default=None),
) -> SandboxRunResultResponse:
    result = sandbox_service.get_result(run_id, x_sandbox_session)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    if result == "not_ready":
        raise HTTPException(status_code=409, detail="Sandbox result is not ready yet.")
    return result

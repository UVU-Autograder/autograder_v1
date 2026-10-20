from fastapi import APIRouter, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.core.dependencies import DbSession
from app.core.settings import get_settings
from app.domains.sandbox.catalog import (
    get_sandbox_assignment,
    list_sandbox_assignments,
    list_sandbox_courses,
)
from app.domains.sandbox.intake import (
    AssignmentNotGradableError,
    AssignmentNotFoundError,
    GraderServiceUnavailableError,
    GradingQueueFullError,
    NetworkRateLimitExceededError,
    SessionQuotaExceededError,
    sandbox_intake_engine,
)
from app.domains.sandbox.schemas import (
    ConceptMetadata,
    SandboxAiFeedbackResponse,
    SandboxAssignmentDetail,
    SandboxAssignmentListResponse,
    SandboxCancelResponse,
    SandboxCourseListResponse,
    SandboxRunCreateResponse,
    SandboxRunResultResponse,
)
from app.domains.sandbox import ip_limit
from app.domains.sandbox.ai_capacity import AiBusy, ai_capacity
from app.domains.sandbox.service import AiFeedbackUnavailable, sandbox_service

# Retry hint for a full grading queue. Admission is checked before the upload is
# counted, so retrying a queue_full response never uses up the student's run limit.
QUEUE_FULL_RETRY_SECONDS = 15

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
    request: Request,
    response: Response,
    course_id: str,
    assignment_id: str,
    bundle: UploadFile = File(...),
    stdin: str | None = Form(default=None),
    x_sandbox_session: str | None = Header(default=None),
) -> SandboxRunCreateResponse:
    """Create a new sandbox run for a submission bundle, with optional stdin input."""
    settings = get_settings()
    if stdin and len(stdin.encode("utf-8")) > 65536:
        raise HTTPException(status_code=400, detail="Console stdin input exceeds maximum allowed size.")
    zip_data = await bundle.read()
    if len(zip_data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Upload exceeds maximum size.")
    # Database and scheduling work is synchronous; keep it off the event loop so a
    # burst of uploads cannot stall status polls and AI requests.
    ip = ip_limit.client_ip(request.client.host if request.client else None, request.headers.get("x-real-ip"))
    return await run_in_threadpool(
        _create_run_sync, db, response, course_id, assignment_id, zip_data, stdin, x_sandbox_session, ip,
    )


def _create_run_sync(
    db,
    response: Response,
    course_id: str,
    assignment_id: str,
    zip_data: bytes,
    stdin: str | None,
    x_sandbox_session: str | None,
    ip: str | None = None,
) -> SandboxRunCreateResponse:
    try:
        result = sandbox_intake_engine.intake_submission(
            db,
            course_id=course_id,
            assignment_id=assignment_id,
            session_id=x_sandbox_session,
            zip_data=zip_data,
            stdin=stdin,
            client_ip=ip,
        )
        response.headers["X-Sandbox-Session"] = result.session_id
        return result.response
    except AssignmentNotFoundError:
        raise HTTPException(status_code=404, detail="Assignment not found.") from None
    except AssignmentNotGradableError as exc:
        if exc.session_id:
            response.headers["X-Sandbox-Session"] = exc.session_id
        raise HTTPException(status_code=400, detail=exc.message) from None
    except NetworkRateLimitExceededError as exc:
        session_id = exc.session_id
        response.headers["X-Sandbox-Session"] = session_id
        raise HTTPException(
            status_code=429,
            detail={
                "code": "network_limit",
                "message": "Too many runs from your network this hour. Please try again later.",
                "reset_at": exc.reset_at,
                "limit": exc.limit,
            },
            headers={"X-Sandbox-Session": session_id},
        ) from None
    except SessionQuotaExceededError as exc:
        session_id = exc.session_id
        response.headers["X-Sandbox-Session"] = session_id
        raise HTTPException(
            status_code=429,
            detail={
                "code": "quota_exhausted",
                "message": f"You have used all {exc.quota.limit} runs for this hour.",
                "reset_at": exc.quota.reset_at,
                "limit": exc.quota.limit,
            },
            headers={"X-Sandbox-Session": session_id},
        ) from None
    except GradingQueueFullError as exc:
        session_header = {"X-Sandbox-Session": exc.session_id} if exc.session_id else {}
        if exc.session_id:
            response.headers["X-Sandbox-Session"] = exc.session_id
        raise HTTPException(
            status_code=503,
            detail={
                "code": "queue_full",
                "message": "The grading queue is full right now. Your run was not counted; retrying automatically.",
                "retry_after_seconds": exc.retry_after_seconds,
            },
            headers={**session_header, "Retry-After": str(exc.retry_after_seconds)},
        ) from None
    except GraderServiceUnavailableError as exc:
        session_header = {"X-Sandbox-Session": exc.session_id} if exc.session_id else {}
        if exc.session_id:
            response.headers["X-Sandbox-Session"] = exc.session_id
        raise HTTPException(
            status_code=503,
            detail={
                "code": exc.code,
                "message": exc.message,
                "retry_after_seconds": exc.retry_after_seconds,
            },
            headers={**session_header, "Retry-After": str(exc.retry_after_seconds)},
        ) from None


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


async def _ai_feedback(run_id: str, session_id: str | None) -> SandboxAiFeedbackResponse:
    """Run the model inside the AI capacity limit; outages become coded HTTP errors."""
    try:
        # Cheap checks (unknown run, grading not finished, grader fault) before taking a slot.
        context = await run_in_threadpool(sandbox_service.ai_feedback_context, run_id, session_id)
        if context is None:
            raise HTTPException(status_code=404, detail="Run not found.")
        feedback = await ai_capacity.run(sandbox_service.generate_ai_feedback, run_id, session_id)
    except AiBusy as busy:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ai_busy",
                "message": "The AI tutor is helping other students. Retrying automatically.",
                "ahead": busy.ahead,
                "retry_after_seconds": busy.retry_after_seconds,
            },
            headers={"Retry-After": str(busy.retry_after_seconds)},
        ) from None
    except AiFeedbackUnavailable as exc:
        headers = {"Retry-After": str(exc.retry_after_seconds)} if exc.retry_after_seconds else None
        raise HTTPException(status_code=exc.status, detail=exc.detail(), headers=headers) from None
    if feedback is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return feedback


@router.post("/runs/{run_id}/ai-feedback", response_model=SandboxAiFeedbackResponse)
async def generate_ai_feedback_endpoint(
    run_id: str,
    x_sandbox_session: str | None = Header(default=None),
) -> SandboxAiFeedbackResponse:
    return await _ai_feedback(run_id, x_sandbox_session)


@router.post("/runs/{run_id}/ai-feedback/stream")
async def generate_ai_feedback_stream_endpoint(
    run_id: str,
    x_sandbox_session: str | None = Header(default=None),
) -> StreamingResponse:
    # Feedback is generated and validated before the first line is sent, so errors
    # still arrive as proper HTTP statuses rather than mid-stream.
    feedback = await _ai_feedback(run_id, x_sandbox_session)
    return StreamingResponse(
        iter(feedback.ai_feedback.splitlines(keepends=True)),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/concepts/metadata", response_model=dict[str, ConceptMetadata])
def get_concepts_metadata_endpoint():
    from app.integrations.ast_checker.validator import get_concepts_metadata
    return get_concepts_metadata()



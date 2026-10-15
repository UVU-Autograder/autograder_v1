from fastapi import APIRouter, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.core.dependencies import DbSession
from app.core.settings import get_settings
from app.domains.assignments.service import (
    effective_allowed_concepts,
    get_assignment_for_course,
)
from app.domains.assignments.validation import run_preflight_validation
from app.domains.sandbox.catalog import (
    get_sandbox_assignment,
    list_sandbox_assignments,
    list_sandbox_courses,
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
    assignment = get_sandbox_assignment(
        db,
        course_id,
        assignment_id,
        sandbox_service.quota_for_session(x_sandbox_session),
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    db_assignment = get_assignment_for_course(db, course_id, assignment_id)
    if db_assignment is None or db_assignment.config is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    preflight_errors = run_preflight_validation(db, course_id, assignment_id)
    if preflight_errors:
        raise HTTPException(
            status_code=400,
            detail="Assignment is not ready for grading. Contact your instructor.",
        )
    from app.domains.assignments.inventory import inventory_status
    if inventory_status(db, db_assignment) != "ready":
        raise HTTPException(status_code=400, detail="Assignment requires instructor reference validation before grading.")

    artifact_refs: dict[str, str] = {}
    for art in db_assignment.artifacts:
        if art.storage_ref:
            artifact_refs[art.artifact_key] = art.storage_ref

    allowed_concepts = effective_allowed_concepts(db_assignment)

    run_config = dict(db_assignment.config.config) if db_assignment.config and db_assignment.config.config else {}
    if db_assignment.description and not run_config.get("description"):
        run_config["description"] = db_assignment.description
    expected_manifest = db_assignment.config.validated_test_manifest if db_assignment.config else None
    max_score = assignment.max_score
    # Hand this request's database connection back before scheduling. Scheduling takes
    # the scheduler lock and then needs its own connection; requests that held a
    # connection while waiting for the lock exhausted the pool under a burst of
    # uploads, so the lock holder stalled and grading workers timed out.
    db.close()

    limited = ip_limit.charge(ip)
    if limited is not None:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "network_limit",
                "message": "Too many runs from your network this hour. Please try again later.",
                "reset_at": limited.reset_at,
                "limit": limited.limit,
            },
        )
    try:
        run, session, error_status = sandbox_service.create_run(
            course_id=course_id,
            assignment_id=assignment_id,
            session_id=x_sandbox_session,
            assignment_exists=True,
            max_score=max_score,
            zip_data=zip_data,
            config=run_config,
            artifact_refs=artifact_refs,
            allowed_concepts=allowed_concepts,
            stdin=stdin,
            expected_manifest=expected_manifest,
        )
    except HTTPException as exc:
        ip_limit.refund(ip)
        if exc.status_code == 503:
            # The scheduler lock or database is momentarily unavailable; nothing was counted.
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "busy",
                    "message": "The grader is busy. Retrying automatically.",
                    "retry_after_seconds": 5,
                },
                headers={"Retry-After": "5"},
            ) from None
        raise
    if error_status is not None:
        ip_limit.refund(ip)  # not admitted, so it does not count against the network either
    response.headers["X-Sandbox-Session"] = session
    session_header = {"X-Sandbox-Session": session}
    if error_status == 429:
        quota = sandbox_service.quota_for_session(session)
        raise HTTPException(
            status_code=429,
            detail={
                "code": "quota_exhausted",
                "message": f"You have used all {quota.limit} runs for this hour.",
                "reset_at": quota.reset_at,
                "limit": quota.limit,
            },
            headers=session_header,
        )
    if error_status == 503:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "queue_full",
                "message": "The grading queue is full right now. Your run was not counted; retrying automatically.",
                "retry_after_seconds": QUEUE_FULL_RETRY_SECONDS,
            },
            headers={**session_header, "Retry-After": str(QUEUE_FULL_RETRY_SECONDS)},
        )
    if error_status == 502:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "grader_unavailable",
                "message": "The grader could not start your run. Please try again in a minute.",
                "retry_after_seconds": 60,
            },
            headers={**session_header, "Retry-After": "60"},
        )
    if run is None:
        raise HTTPException(status_code=500, detail="Failed to initialize sandbox run.")
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



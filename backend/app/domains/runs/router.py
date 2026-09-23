import base64
import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.audit_log import audit_event
from app.core.dependencies import (
    DbSession,
    accessible_section_ids_for_course,
    assert_run_section_access,
    get_optional_user,
    require_staff,
)
from app.domains.auth.models import User
from app.domains.runs.models import RunSummary
from app.domains.runs import retention
from app.domains.runs.orchestrator import get_run_state
from app.domains.runs.queue_admission import (
    backpressure_snapshot,
    eta_band_for_position,
)
from app.domains.runs.schemas import (
    RunCounters,
    RunStatusResponse,
    RunSummaryListResponse,
    RunSummaryResponse,
    UpdateManualGradesRequest,
)
from app.domains.runs.service import (
    is_listable_student_file,
    load_run_details_json,
    manual_grading_progress,
    mutate_run_details,
    official_run_dir,
    require_official_run_for_assignment,
    student_detail_from_result,
    student_workspace_dir,
    update_student_manual_result,
)
from app.domains.sandbox.service import sandbox_service

router = APIRouter(prefix="/runs", tags=["runs"])

MAX_PREVIEW_BYTES = 1 * 1024 * 1024
NON_PREVIEWABLE_SUFFIXES = (
    ".pyc", ".zip", ".exe", ".pdf", ".tar", ".gz",
)
IMAGE_PREVIEW_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp"})


def _preview_kind(path: Path, size_bytes: int) -> str:
    if size_bytes > MAX_PREVIEW_BYTES:
        return "none"
    suffix = path.suffix.lower()
    if suffix in NON_PREVIEWABLE_SUFFIXES:
        return "none"
    if suffix in IMAGE_PREVIEW_SUFFIXES:
        return "image"
    return "text"


def _is_file_previewable(path: Path, size_bytes: int) -> bool:
    return _preview_kind(path, size_bytes) != "none"


def _image_content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed and guessed.startswith("image/"):
        return guessed
    return "application/octet-stream"


def _load_official_run_details(run_id: int) -> dict:
    details_file = official_run_dir(run_id) / "run_details.json"
    if not details_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Run details are not available or have been cleaned up.",
        )
    return load_run_details_json(details_file)


def _require_exports_ready(run_id: int, *, run_status: str) -> None:
    data = _load_official_run_details(run_id)
    progress = manual_grading_progress(
        data.get("student_results", {}),
        run_status=run_status,
    )
    if not progress["exports_ready"]:
        raise HTTPException(
            status_code=409,
            detail="Exports are available only after the run completes and every manual rubric score is set.",
        )


def _retained_download(run_id: int, *, path: Path, filename: str, media_type: str) -> StreamingResponse:
    snapshot = path.stat()
    length = snapshot.st_size

    def chunks():
        offset = 0
        while offset < length:
            with retention.access(run_id):
                current = path.stat()
                if (current.st_ino, current.st_mtime_ns, current.st_size) != (snapshot.st_ino, snapshot.st_mtime_ns, snapshot.st_size):
                    raise RuntimeError("Export changed. Download again.")
                with path.open("rb") as handle:
                    handle.seek(offset)
                    chunk = handle.read(min(65536, length - offset))
            if not chunk:
                raise RuntimeError("Export is no longer available.")
            offset += len(chunk)
            yield chunk

    return StreamingResponse(chunks(), media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(length), "Cache-Control": "no-store",
    })


def _official_status_from_run(run: RunSummary, redis_state: dict | None) -> RunStatusResponse:
    from app.db.session import SessionLocal
    from app.domains.runs.models import OfficialDispatch
    from app.domains.runs.queue_admission import ticket_state
    with SessionLocal() as scheduling_db:
        bounded = scheduling_db.get(OfficialDispatch, run.id) is not None
    if bounded:
        redis_state = None  # Redis may predate a committed workspace checkpoint.
    bp = backpressure_snapshot()
    if redis_state is not None:
        state = redis_state.get("state", run.status)
        if state not in ("queue", "run", "complete", "failure"):
            state = "complete"
        queue_position = redis_state.get("queue_position") if state == "queue" else None
        eta = redis_state.get("eta_band") if state == "queue" else None
        if state == "queue" and eta is None:
            eta = eta_band_for_position(queue_position)
        counters = RunCounters(
            total=int(redis_state.get("total", run.total_submission_count or 0)),
            queued=int(redis_state.get("queued", 0)),
            running=int(redis_state.get("running", 0)),
            completed=int(redis_state.get("completed", 0)),
            failed=int(redis_state.get("failed", 0)),
            warnings=int(redis_state.get("warnings", 0)),
        )
        message = redis_state.get("message") or f"Official run status: {state}"
    else:
        state = run.status if run.status in ("queue", "run", "complete", "failure") else "complete"
        completed = run.success_count + run.warning_count
        failed = run.failure_count + run.timeout_count
        queue_position = None
        eta = None
        active = int(state == "run" and (not bounded or ticket_state(f"official:{run.id}") == "active"))
        remaining = max(0, run.total_submission_count - completed - failed)
        counters = RunCounters(
            total=run.total_submission_count,
            queued=max(0, remaining - active) if state in ("queue", "run") else 0,
            running=active if bounded else (remaining if state == "run" else 0),
            completed=completed,
            failed=failed,
            warnings=run.warning_count,
        )
        message = f"Official run status: {run.status}"

    if not retention.available(run) and state in ("queue", "run"):
        state = "failure"
        message = "Official review expired or is unavailable."
        counters.queued = 0
        counters.running = 0
        queue_position = None
        eta = None

    return RunStatusResponse(
        run_id=str(run.id),
        state=state,
        queue_position=queue_position,
        eta_band=eta,
        counters=counters,
        backpressure=bp,
        message=message,
    )


@router.get("/{run_id}/status", response_model=RunStatusResponse)
def get_run_status(
    run_id: str,
    db: DbSession,
    current_user: User | None = Depends(get_optional_user),
) -> RunStatusResponse:
    # Official numeric IDs require staff + section access.
    if run_id.isdigit():
        if current_user is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication credentials were not provided.",
            )
        user_roles = {
            access.role.name for access in current_user.staff_access if access.is_active
        }
        if not user_roles.intersection({"admin", "instructor", "IA"}):
            raise HTTPException(status_code=403, detail="Staff access required.")

        run = db.scalar(select(RunSummary).where(RunSummary.id == int(run_id)))
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found.")

        from sqlalchemy.orm import selectinload

        from app.domains.assignments.models import Assignment

        assignment = db.scalar(
            select(Assignment)
            .where(Assignment.id == run.assignment_id)
            .options(selectinload(Assignment.course))
        )
        if assignment is None:
            raise HTTPException(status_code=404, detail="Run not found.")

        assert_run_section_access(
            db,
            current_user,
            course_code=assignment.course.code,
            section_id=run.section_id,
        )
        redis_state = None
        try:
            redis_state = get_run_state(run_id)
        except Exception:
            redis_state = None
        return _official_status_from_run(run, redis_state)

    # Sandbox runs remain unauthenticated (session gate is on result/cancel).
    status = sandbox_service.get_status(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return status


staff_runs_router = APIRouter(
    prefix="/staff/courses/{course_id}/assignments/{assignment_id}/runs",
    tags=["staff-runs"],
    dependencies=[Depends(require_staff)],
)


@staff_runs_router.get("", response_model=RunSummaryListResponse)
def list_official_runs(
    course_id: str,
    assignment_id: str,
    db: DbSession,
    current_user: User = Depends(require_staff),
) -> RunSummaryListResponse:
    from app.domains.assignments.service import get_assignment_for_course

    assignment = get_assignment_for_course(db, course_id, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    query = (
        select(RunSummary)
        .where(
            RunSummary.assignment_id == assignment.id,
            RunSummary.workflow_type == "official",
        )
        .order_by(RunSummary.created_at.desc())
    )
    allowed = accessible_section_ids_for_course(db, current_user, course_id)
    if allowed is not None:
        query = query.where(RunSummary.section_id.in_(allowed))

    runs = db.scalars(query).all()
    return RunSummaryListResponse(runs=[RunSummaryResponse.model_validate(r) for r in runs])


@staff_runs_router.get("/{run_id}", response_model=RunSummaryResponse)
def get_official_run(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
    current_user: User = Depends(require_staff),
) -> RunSummaryResponse:
    run = require_official_run_for_assignment(
        db, course_id, assignment_id, run_id, user=current_user
    )
    return RunSummaryResponse.model_validate(run)


@staff_runs_router.get("/{run_id}/details")
def get_official_run_details(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
    current_user: User = Depends(require_staff),
):
    run = require_official_run_for_assignment(
        db, course_id, assignment_id, run_id, user=current_user
    )
    with retention.access(run_id, db):
        data = _load_official_run_details(run_id)
        students = [
            student_detail_from_result(canvas_id, res)
            for canvas_id, res in data.get("student_results", {}).items()
        ]
        students.sort(key=lambda student: student["student_name"].casefold())
        progress = manual_grading_progress(
            data.get("student_results", {}),
            run_status=run.status,
        )

        return {
            "run_id": run_id,
            "status": run.status,
            "students": students,
            **progress,
        }


@staff_runs_router.get("/{run_id}/export/csv")
def export_official_run_csv(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
    current_user: User = Depends(require_staff),
):
    run = require_official_run_for_assignment(
        db, course_id, assignment_id, run_id, user=current_user
    )
    with retention.access(run_id, db):
        _require_exports_ready(run_id, run_status=run.status)
        csv_file = official_run_dir(run_id) / "grades.csv"

        if not csv_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Grades CSV file is not available or have been cleaned up.",
            )

        return _retained_download(run_id,
            path=csv_file,
            filename=f"assignment_{assignment_id}_run_{run_id}_grades.csv",
            media_type="text/csv",
        )


@staff_runs_router.get("/{run_id}/export/feedback")
def export_official_run_feedback(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
    current_user: User = Depends(require_staff),
):
    run = require_official_run_for_assignment(
        db, course_id, assignment_id, run_id, user=current_user
    )
    with retention.access(run_id, db):
        _require_exports_ready(run_id, run_status=run.status)
        zip_file = official_run_dir(run_id) / "feedback.zip"

        if not zip_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Feedback ZIP file is not available or have been cleaned up.",
            )

        return _retained_download(run_id,
            path=zip_file,
            filename=f"assignment_{assignment_id}_run_{run_id}_feedback.zip",
            media_type="application/zip",
        )


@staff_runs_router.post("/{run_id}/cleanup")
def cleanup_official_run(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
    current_user: User = Depends(require_staff),
):
    require_official_run_for_assignment(
        db, course_id, assignment_id, run_id, user=current_user
    )
    try:
        deleted = retention.cleanup(run_id, db, manual=True)
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(503, "Cleanup is unavailable. Retry later.") from None
    if not deleted:
        raise HTTPException(503, "Cleanup did not finish. Review access is disabled and cleanup will retry.")

    audit_event(
        "official.workspace_manual_cleanup",
        run_id=run_id,
        course_id=course_id,
        assignment_id=assignment_id,
        actor_user_id=current_user.id,
        workflow_type="official",
    )

    return {"message": "Run workspace cleaned up successfully."}


@staff_runs_router.get("/{run_id}/students/{canvas_id}/files")
def list_student_files(
    course_id: str,
    assignment_id: str,
    run_id: int,
    canvas_id: str,
    db: DbSession,
    current_user: User = Depends(require_staff),
):
    require_official_run_for_assignment(
        db, course_id, assignment_id, run_id, user=current_user
    )
    with retention.access(run_id, db):
        student_dir = student_workspace_dir(run_id, canvas_id)

        if not student_dir.exists():
            raise HTTPException(
                status_code=404,
                detail="Student workspace files are not available or have been cleaned up.",
            )

        files = []
        for path in student_dir.rglob("*"):
            if not path.is_file() or not is_listable_student_file(path, student_dir):
                continue
            stat = path.stat()
            rel_path = str(path.relative_to(student_dir)).replace("\\", "/")
            kind = _preview_kind(path, stat.st_size)
            files.append({
                "filepath": rel_path,
                "size_bytes": stat.st_size,
                "previewable": kind != "none",
                "preview_kind": kind,
            })

        return {"files": files}


@staff_runs_router.get("/{run_id}/students/{canvas_id}/files/content")
def get_student_file_content(
    course_id: str,
    assignment_id: str,
    run_id: int,
    canvas_id: str,
    filepath: str,
    db: DbSession,
    current_user: User = Depends(require_staff),
):
    require_official_run_for_assignment(
        db, course_id, assignment_id, run_id, user=current_user
    )
    with retention.access(run_id, db):
        student_dir = student_workspace_dir(run_id, canvas_id).resolve()

        if not student_dir.exists():
            raise HTTPException(
                status_code=404,
                detail="Student workspace files are not available or have been cleaned up.",
            )

        target_path = (student_dir / filepath).resolve()
        try:
            target_path.relative_to(student_dir)
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Directory traversal detected.",
            )

        if not target_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Requested file not found in student workspace.",
            )

        stat = target_path.stat()
        kind = _preview_kind(target_path, stat.st_size)
        if kind == "none":
            raise HTTPException(
                status_code=400,
                detail="File is not previewable.",
            )

        if kind == "image":
            raw = target_path.read_bytes()
            return {
                "kind": "image",
                "content_type": _image_content_type(target_path),
                "content_base64": base64.b64encode(raw).decode("ascii"),
            }

        try:
            content = target_path.read_text(encoding="utf-8")
            return {"kind": "text", "content": content}
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File is not a valid text file.",
            )


@staff_runs_router.post("/{run_id}/students/{canvas_id}/manual-grades")
def update_student_manual_grades(
    course_id: str,
    assignment_id: str,
    run_id: int,
    canvas_id: str,
    req: UpdateManualGradesRequest,
    db: DbSession,
    current_user: User = Depends(require_staff),
):
    run = require_official_run_for_assignment(
        db, course_id, assignment_id, run_id, user=current_user
    )
    with retention.access(run_id, db):
        from app.domains.grading.engine import GradingResult
        from app.domains.runs.feedback_formatter import generate_pedagogical_feedback_html

        def apply_update(data: dict) -> dict:
            student_results = data.get("student_results", {})
            if canvas_id not in student_results:
                raise HTTPException(
                    status_code=404,
                    detail="Student not found in this run.",
                )
            result = student_results[canvas_id]
            update_student_manual_result(
                result,
                {
                    key: value.model_dump()
                    for key, value in req.grades.items()
                },
                overall_comment=req.overall_comment,
                update_overall_comment="overall_comment" in req.model_fields_set,
            )
            grading_result = GradingResult(
                success=result["success"],
                failure_category=result["failure_category"],
                failure_message=result["failure_message"],
                score=result["score"],
                max_score=result["max_score"],
                test_results=result["test_results"],
                warnings=result["warnings"],
            )
            result["feedback_html"] = generate_pedagogical_feedback_html(
                result["student_identifier"],
                grading_result,
                result["manual_results"],
                result.get("overall_comment", ""),
            )
            return result

        data, result = mutate_run_details(run_id, apply_update)
        response = student_detail_from_result(canvas_id, result)
        response["manual_progress"] = manual_grading_progress(
            data.get("student_results", {}),
            run_status=run.status,
        )
        return response

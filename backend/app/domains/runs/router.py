from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from pathlib import Path
import json
import shutil

from app.core.dependencies import DbSession, require_staff
from app.domains.runs.schemas import (
    RunStatusResponse,
    RunSummaryResponse,
    RunSummaryListResponse,
    RunCounters,
    QueueBackpressure,
    UpdateManualGradesRequest,
)
from app.domains.sandbox.service import sandbox_service
from app.domains.runs.models import RunSummary
from app.domains.runs.service import (
    is_listable_student_file,
    load_run_details_json,
    official_run_dir,
    official_run_zip_path,
    require_official_run_for_assignment,
    student_detail_from_result,
    student_workspace_dir,
    write_feedback_zip,
    write_run_grades_csv,
)

router = APIRouter(prefix="/runs", tags=["runs"])

MAX_PREVIEW_BYTES = 1 * 1024 * 1024
NON_PREVIEWABLE_SUFFIXES = (
    ".pyc", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".exe", ".pdf", ".tar", ".gz",
)


def _is_file_previewable(path: Path, size_bytes: int) -> bool:
    if size_bytes > MAX_PREVIEW_BYTES:
        return False
    return path.suffix.lower() not in NON_PREVIEWABLE_SUFFIXES


@router.get("/{run_id}/status", response_model=RunStatusResponse)
def get_run_status(run_id: str, db: DbSession) -> RunStatusResponse:
    if run_id.isdigit():
        run = db.scalar(select(RunSummary).where(RunSummary.id == int(run_id)))
        if run:
            state_val = run.status
            if state_val not in ("queue", "run", "complete", "failure"):
                state_val = "complete"
            return RunStatusResponse(
                run_id=run_id,
                state=state_val,
                queue_position=None,
                eta_band=None,
                counters=RunCounters(total=0, queued=0, running=0, completed=0, failed=0, warnings=0),
                backpressure=QueueBackpressure(current_waiting=0, high_load=False, accepting_runs=True),
                message=f"Official run status: {run.status}",
            )

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
) -> RunSummaryListResponse:
    from app.domains.assignments.service import get_assignment_for_course
    assignment = get_assignment_for_course(db, course_id, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    runs = db.scalars(
        select(RunSummary)
        .where(
            RunSummary.assignment_id == assignment.id,
            RunSummary.workflow_type == "official",
        )
        .order_by(RunSummary.created_at.desc())
    ).all()

    return RunSummaryListResponse(runs=[RunSummaryResponse.model_validate(r) for r in runs])


@staff_runs_router.get("/{run_id}", response_model=RunSummaryResponse)
def get_official_run(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
) -> RunSummaryResponse:
    run = require_official_run_for_assignment(db, course_id, assignment_id, run_id)
    return RunSummaryResponse.model_validate(run)


@staff_runs_router.get("/{run_id}/details")
def get_official_run_details(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
):
    run = require_official_run_for_assignment(db, course_id, assignment_id, run_id)
    details_file = official_run_dir(run_id) / "run_details.json"

    if not details_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Run details are not available or have been cleaned up.",
        )

    data = load_run_details_json(details_file)
    students = [
        student_detail_from_result(canvas_id, res)
        for canvas_id, res in data.get("student_results", {}).items()
    ]

    return {
        "run_id": run_id,
        "status": run.status,
        "students": students,
    }


@staff_runs_router.get("/{run_id}/export/csv")
def export_official_run_csv(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
):
    require_official_run_for_assignment(db, course_id, assignment_id, run_id)
    csv_file = official_run_dir(run_id) / "grades.csv"

    if not csv_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Grades CSV file is not available or has been cleaned up.",
        )

    return FileResponse(
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
):
    require_official_run_for_assignment(db, course_id, assignment_id, run_id)
    zip_file = official_run_dir(run_id) / "feedback.zip"

    if not zip_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Feedback ZIP file is not available or has been cleaned up.",
        )

    return FileResponse(
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
):
    require_official_run_for_assignment(db, course_id, assignment_id, run_id)
    run_dir = official_run_dir(run_id)
    zip_file = official_run_zip_path(run_id)

    if run_dir.exists():
        shutil.rmtree(run_dir, ignore_errors=True)
    if zip_file.exists():
        zip_file.unlink(missing_ok=True)

    return {"message": "Run workspace cleaned up successfully."}


@staff_runs_router.get("/{run_id}/students/{canvas_id}/files")
def list_student_files(
    course_id: str,
    assignment_id: str,
    run_id: int,
    canvas_id: str,
    db: DbSession,
):
    require_official_run_for_assignment(db, course_id, assignment_id, run_id)
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
        files.append({
            "filepath": rel_path,
            "size_bytes": stat.st_size,
            "previewable": _is_file_previewable(path, stat.st_size),
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
):
    require_official_run_for_assignment(db, course_id, assignment_id, run_id)
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
    if not _is_file_previewable(target_path, stat.st_size):
        raise HTTPException(
            status_code=400,
            detail="File is not previewable.",
        )

    try:
        content = target_path.read_text(encoding="utf-8")
        return {"content": content}
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
):
    require_official_run_for_assignment(db, course_id, assignment_id, run_id)
    run_dir = official_run_dir(run_id)
    details_file = run_dir / "run_details.json"

    if not details_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Run details are not available or have been cleaned up.",
        )

    data = load_run_details_json(details_file)
    student_results = data.get("student_results", {})
    if canvas_id not in student_results:
        raise HTTPException(status_code=404, detail="Student not found in this run.")

    res = student_results[canvas_id]
    manual_results = res.get("manual_results", {})

    for key, val in req.grades.items():
        if key not in manual_results:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid manual rubric item key: {key}",
            )
        max_points = manual_results[key]["points"]
        if val.score is not None and val.score > max_points:
            raise HTTPException(
                status_code=400,
                detail=f"Score {val.score} exceeds maximum points of {max_points} for key {key}.",
            )
        manual_results[key]["score"] = val.score
        manual_results[key]["comments"] = val.comments or ""

    res["manual_results"] = manual_results

    from app.domains.grading.service import GradingResult
    from app.domains.runs.tasks import generate_pedagogical_feedback_html

    grading_result = GradingResult(
        success=res["success"],
        failure_category=res["failure_category"],
        failure_message=res["failure_message"],
        score=res["score"],
        max_score=res["max_score"],
        test_results=res["test_results"],
        warnings=res["warnings"],
    )
    feedback_html = generate_pedagogical_feedback_html(
        res["student_identifier"],
        grading_result,
        manual_results,
    )
    res["feedback_html"] = feedback_html

    details_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    write_run_grades_csv(run_dir, student_results)
    write_feedback_zip(run_dir, student_results)

    return student_detail_from_result(canvas_id, res, feedback_html=feedback_html)

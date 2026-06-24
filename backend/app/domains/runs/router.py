from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select
from pathlib import Path
import json
import shutil

from app.core.dependencies import DbSession, require_staff
from app.domains.runs.schemas import RunStatusResponse, RunSummaryResponse, RunSummaryListResponse, RunCounters, QueueBackpressure
from app.domains.sandbox.service import sandbox_service
from app.domains.runs.models import RunSummary
from app.core.settings import get_settings

router = APIRouter(prefix="/runs", tags=["runs"])

# Main runs status query endpoint (used by both sandbox and official flows)
@router.get("/{run_id}/status", response_model=RunStatusResponse)
def get_run_status(run_id: str, db: DbSession) -> RunStatusResponse:
    # 1. Check if numeric ID (official run)
    if run_id.isdigit():
        run = db.scalar(select(RunSummary).where(RunSummary.id == int(run_id)))
        if run:
            state_val = run.status
            if state_val not in ("queue", "run", "complete", "failure"):
                state_val = "complete"  # fallback
            return RunStatusResponse(
                run_id=run_id,
                state=state_val,
                queue_position=None,
                eta_band=None,
                counters=RunCounters(total=0, queued=0, running=0, completed=0, failed=0, warnings=0),
                backpressure=QueueBackpressure(current_waiting=0, high_load=False, accepting_runs=True),
                message=f"Official run status: {run.status}",
            )

    # 2. Sandbox flow
    status = sandbox_service.get_status(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return status


# Staff runs management router
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
    from app.domains.assignments.service import get_assignment_for_course
    assignment = get_assignment_for_course(db, course_id, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    run = db.scalar(
        select(RunSummary).where(
            RunSummary.id == run_id,
            RunSummary.assignment_id == assignment.id,
        )
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    return RunSummaryResponse.model_validate(run)


@staff_runs_router.get("/{run_id}/details")
def get_official_run_details(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
):
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    details_file = workspaces_dir / f"official_{run_id}" / "run_details.json"

    if not details_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Run details are not available or have been cleaned up.",
        )

    try:
        data = json.loads(details_file.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to load run details.")

    run_summary = db.scalar(select(RunSummary).where(RunSummary.id == run_id))
    status = run_summary.status if run_summary else "unknown"

    students = []
    student_results = data.get("student_results", {})
    for canvas_id, res in student_results.items():
        success = res.get("success", False)
        warnings = res.get("warnings", [])
        
        status_val = "failure"
        if success:
            status_val = "warning" if warnings else "success"

        if not success:
            feedback_preview = res.get("failure_message") or "Grading execution failed."
        elif warnings:
            feedback_preview = "; ".join([w.get("message") for w in warnings if w.get("message")])
        else:
            feedback_preview = "All tests passed successfully."

        students.append({
            "student_name": res.get("student_identifier", "Unknown"),
            "canvas_id": canvas_id,
            "matched_file": res.get("matched_file") or "student_functions.py",
            "score": res.get("score", 0),
            "max_score": res.get("max_score", 100),
            "status": status_val,
            "feedback_preview": feedback_preview
        })

    return {
        "run_id": run_id,
        "status": status,
        "students": students
    }


@staff_runs_router.get("/{run_id}/export/csv")
def export_official_run_csv(
    course_id: str,
    assignment_id: str,
    run_id: int,
    db: DbSession,
):
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    csv_file = workspaces_dir / f"official_{run_id}" / "grades.csv"

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
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    zip_file = workspaces_dir / f"official_{run_id}" / "feedback.zip"

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
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    run_dir = workspaces_dir / f"official_{run_id}"
    zip_file = workspaces_dir / f"official_{run_id}.zip"

    deleted = False
    if run_dir.exists():
        shutil.rmtree(run_dir, ignore_errors=True)
        deleted = True
    if zip_file.exists():
        zip_file.unlink(missing_ok=True)
        deleted = True

    if not deleted:
        raise HTTPException(status_code=404, detail="Workspace files not found.")

    return {"message": "Run workspace cleaned up successfully."}

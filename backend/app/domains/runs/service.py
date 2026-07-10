from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.domains.runs.models import RunSummary

EXCLUDED_WORKSPACE_PARTS = frozenset({"__pycache__", ".DS_Store"})


def get_workspaces_dir() -> Path:
    return get_settings().artifact_storage_path.parent / "workspaces"


def official_run_zip_path(run_id: int) -> Path:
    return get_workspaces_dir() / f"official_{run_id}.zip"


def official_run_dir(run_id: int) -> Path:
    return get_workspaces_dir() / f"official_{run_id}"


def student_workspace_dir(run_id: int, canvas_id: str) -> Path:
    return official_run_dir(run_id) / f"student_{canvas_id}"


def manual_score_sum(manual_results: dict | None) -> int:
    if not manual_results:
        return 0
    return sum(
        m.get("score") or 0
        for m in manual_results.values()
        if m.get("score") is not None
    )


def init_manual_results(manual_rubric_items) -> dict:
    return {
        item.key: {
            "label": item.label,
            "points": item.points,
            "score": None,
            "comments": "",
        }
        for item in manual_rubric_items
    }


def student_detail_from_result(
    canvas_id: str,
    res: dict,
    *,
    feedback_html: str | None = None,
) -> dict:
    success = res.get("success", False)
    warnings = res.get("warnings", [])
    if not success:
        status_val = "failure"
        feedback_preview = res.get("failure_message") or "Grading execution failed."
    elif warnings:
        status_val = "warning"
        feedback_preview = "; ".join(
            w.get("message") for w in warnings if w.get("message")
        )
    else:
        status_val = "success"
        feedback_preview = "All tests passed successfully."

    manual_results = res.get("manual_results") or {}
    return {
        "student_name": res.get("student_identifier", "Unknown"),
        "canvas_id": canvas_id,
        "matched_file": res.get("matched_file") or "student_functions.py",
        "score": res.get("score", 0) + manual_score_sum(manual_results),
        "max_score": res.get("max_score", 100),
        "status": status_val,
        "feedback_preview": feedback_preview,
        "feedback_html": feedback_html if feedback_html is not None else (res.get("feedback_html") or ""),
        "manual_results": manual_results,
    }


def load_run_details_json(details_file: Path) -> dict:
    try:
        return json.loads(details_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raise HTTPException(status_code=500, detail="Failed to load run details.")


def write_run_grades_csv(run_dir: Path, student_results: dict) -> None:
    with open(run_dir / "grades.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Student Identifier", "Canvas User ID", "Submission ID", "Score", "Max Score"])
        for canvas_id, res in student_results.items():
            writer.writerow([
                res["student_identifier"],
                canvas_id,
                res["submission_id"],
                res.get("score", 0) + manual_score_sum(res.get("manual_results")),
                res["max_score"],
            ])


def write_feedback_zip(run_dir: Path, student_results: dict) -> None:
    with zipfile.ZipFile(run_dir / "feedback.zip", "w", zipfile.ZIP_DEFLATED) as z_out:
        for canvas_id, res in student_results.items():
            filename = f"{res['student_identifier']}_{canvas_id}_feedback.html"
            z_out.writestr(filename, res["feedback_html"])


def is_listable_student_file(path: Path, student_dir: Path) -> bool:
    rel_parts = path.relative_to(student_dir).parts
    return not any(part in EXCLUDED_WORKSPACE_PARTS for part in rel_parts)


def require_official_run_for_assignment(
    db: Session,
    course_id: str,
    assignment_id: str,
    run_id: int,
) -> RunSummary:
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
    return run

from __future__ import annotations

import csv
import json
import os
import threading
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.domains.runs.models import RunSummary

EXCLUDED_WORKSPACE_PARTS = frozenset({"__pycache__", ".DS_Store"})
_RUN_LOCKS: dict[int, threading.Lock] = {}
_RUN_LOCKS_GUARD = threading.Lock()


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


def is_listable_student_file(path: Path, student_dir: Path) -> bool:
    rel_parts = path.relative_to(student_dir).parts
    return not any(part in EXCLUDED_WORKSPACE_PARTS for part in rel_parts)


def list_bundle_files(student_dir: Path) -> list[str]:
    student_dir = Path(student_dir).resolve()
    return sorted(
        str(path.relative_to(student_dir)).replace("\\", "/")
        for path in student_dir.rglob("*")
        if path.is_file() and is_listable_student_file(path, student_dir)
    )


def automated_review_status(res: dict) -> tuple[str, str]:
    """Return UI status and preview text for an automated grading outcome."""
    if not res.get("success", False):
        return "failure", res.get("failure_message") or "Grading execution failed."

    warnings = res.get("warnings", [])
    if warnings:
        preview = "; ".join(message for message in (w.get("message") for w in warnings) if message)
        return "warning", preview or "Grading completed with warnings."

    automated_score = res.get("score", 0)
    automated_max = res.get("automated_max_score", res.get("max_score", 0))
    if automated_max > 0 and automated_score < automated_max:
        failed_labels = [
            item.get("label") or item.get("key")
            for item in res.get("test_results", [])
            if not item.get("passed")
        ]
        if failed_labels:
            shown = ", ".join(label for label in failed_labels[:3] if label)
            suffix = f" (+{len(failed_labels) - 3} more)" if len(failed_labels) > 3 else ""
            return "warning", (
                f"Partial automated score ({automated_score}/{automated_max} pts). "
                f"Did not pass: {shown}{suffix}."
            )
        return "warning", f"Partial automated score ({automated_score}/{automated_max} pts)."

    return "success", "All automated tests passed successfully."


def init_manual_results(scoring_items) -> dict:
    return {
        item.key: {
            "label": item.label,
            "points": item.points,
            "score": None,
            "comments": "",
        }
        for item in scoring_items
        if getattr(item, "item_type", None) == "manual"
    }


def manual_grading_progress(
    student_results: dict,
    *,
    run_status: str | None = None,
) -> dict[str, int | bool]:
    total = len(student_results)
    requires_manual = any(
        bool(result.get("manual_results")) for result in student_results.values()
    )
    completed = sum(
        1
        for result in student_results.values()
        if all(
            item.get("score") is not None
            for item in (result.get("manual_results") or {}).values()
        )
    )
    manual_complete = not requires_manual or completed == total
    run_complete = run_status is None or run_status == "complete"
    return {
        "requires_manual_grading": requires_manual,
        "completed_students": completed,
        "total_students": total,
        "exports_ready": bool(run_complete and manual_complete),
    }


def update_student_manual_result(
    result: dict,
    grade_updates: dict[str, dict[str, Any]],
    *,
    overall_comment: str | None = None,
    update_overall_comment: bool = False,
) -> None:
    manual_results = result.get("manual_results") or {}
    for key, update in grade_updates.items():
        if key not in manual_results:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid manual rubric item key: {key}",
            )
        score = update.get("score")
        max_points = manual_results[key]["points"]
        if score is not None and (
            isinstance(score, bool)
            or not isinstance(score, int)
            or score < 0
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Score for {key} must be a whole number from 0 to "
                    f"{max_points}, or null."
                ),
            )
        if score is not None and score > max_points:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Score {score} exceeds maximum points of "
                    f"{max_points} for key {key}."
                ),
            )
        manual_results[key]["score"] = score
        manual_results[key]["comments"] = update.get("comments") or ""

    result["manual_results"] = manual_results
    if update_overall_comment:
        result["overall_comment"] = overall_comment or ""


def mutate_run_details(
    run_id: int,
    mutator: Callable[[dict], Any],
) -> tuple[dict, Any]:
    """Atomically mutate one run's ephemeral details.

    The lock is process-local. A multi-API-process deployment must replace it
    with a Redis-backed distributed lock.
    """
    with _RUN_LOCKS_GUARD:
        lock = _RUN_LOCKS.setdefault(run_id, threading.Lock())

    run_dir = official_run_dir(run_id)
    details_file = run_dir / "run_details.json"
    with lock:
        if not details_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Run details are not available or have been cleaned up.",
            )
        data = load_run_details_json(details_file)
        result = mutator(data)
        temp_file = details_file.with_suffix(".json.tmp")
        temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(temp_file, details_file)
        student_results = data.get("student_results", {})
        write_run_grades_csv(run_dir, student_results)
        write_feedback_zip(run_dir, student_results)
        return data, result


def student_detail_from_result(
    canvas_id: str,
    res: dict,
    *,
    feedback_html: str | None = None,
) -> dict:
    manual_results = res.get("manual_results") or {}
    status_val, feedback_preview = automated_review_status(res)
    automated_results = [
        {
            "key": item.get("key"),
            "label": item.get("label", item.get("key", "Test Case")),
            "outcome": item.get("outcome"),
            "passed": item.get("passed"),
            "points_awarded": item.get("points_awarded", 0),
            "points": item.get("points", 0),
        }
        for item in res.get("test_results", [])
    ]
    bundle_files = res.get("bundle_files") or []
    return {
        "student_name": res.get("student_identifier", "Unknown"),
        "canvas_id": canvas_id,
        "bundle_files": bundle_files,
        "bundle_file_count": res.get("bundle_file_count", len(bundle_files)),
        "score": res.get("score", 0) + manual_score_sum(manual_results),
        "max_score": res.get("max_score", 100),
        "status": status_val,
        "feedback_preview": feedback_preview,
        "feedback_html": feedback_html if feedback_html is not None else (res.get("feedback_html") or ""),
        "manual_results": manual_results,
        "overall_comment": res.get("overall_comment", ""),
        "automated_results": automated_results,
        "automated_score": res.get("score", 0),
        "automated_max_score": res.get(
            "automated_max_score",
            res.get("max_score", 0)
            - sum(item.get("points", 0) for item in manual_results.values()),
        ),
    }


def load_run_details_json(details_file: Path) -> dict:
    try:
        return json.loads(details_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raise HTTPException(status_code=500, detail="Failed to load run details.")


def write_run_details_json(run_dir: Path, payload: dict) -> None:
    """Atomically write ephemeral official run details."""
    details_file = run_dir / "run_details.json"
    temp_file = details_file.with_suffix(".json.tmp")
    temp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temp_file, details_file)


def write_run_grades_csv(run_dir: Path, student_results: dict) -> None:
    output = run_dir / "grades.csv"
    temp = output.with_suffix(".csv.tmp")
    with open(temp, "w", newline="", encoding="utf-8") as f:
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
    os.replace(temp, output)


def write_feedback_zip(run_dir: Path, student_results: dict) -> None:
    output = run_dir / "feedback.zip"
    temp = output.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as z_out:
        for canvas_id, res in student_results.items():
            filename = f"{res['student_identifier']}_{canvas_id}_feedback.html"
            z_out.writestr(filename, res["feedback_html"])
    os.replace(temp, output)


def require_official_run_for_assignment(
    db: Session,
    course_id: str,
    assignment_id: str,
    run_id: int,
    *,
    user=None,
) -> RunSummary:
    from fastapi import HTTPException

    from app.core.dependencies import assert_run_section_access
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

    if user is not None:
        assert_run_section_access(
            db, user, course_code=course_id, section_id=run.section_id
        )
    return run

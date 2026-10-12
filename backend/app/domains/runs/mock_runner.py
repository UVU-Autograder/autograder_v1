"""Mock runner helper for offline development and testing.

Simulates official run execution without requiring live Judge0 or Celery workers.
"""
from __future__ import annotations

import json

from sqlalchemy import select

from app.db.session import SessionLocal
from app.domains.runs.models import RunSummary
from app.domains.runs import retention
from app.domains.runs.grading_package import GradingPackageError, load_package
from app.domains.runs.orchestrator import set_run_state
from app.domains.runs.queue_admission import release_execution_slots
from app.domains.runs.service import (
    init_manual_results,
    official_run_dir,
    write_feedback_zip,
    write_run_grades_csv,
)


def run_mock_official_run(run_id: int) -> None:
    """Synchronously populate mock database results and ephemeral files for offline testing."""
    with SessionLocal() as db:
        run = db.scalar(select(RunSummary).where(RunSummary.id == run_id))
        if not run:
            return

        with retention.access(run_id, db):
            if run.status != "queue":
                return
            try:
                package = load_package(run_id, assignment_id=run.assignment_id)
            except GradingPackageError as exc:
                run.status = "failure"
                run.failure_summary = {"error": exc.category}
                db.commit()
                return
            run.status = "run"
            db.commit()

        config = package.config
        max_score = config.base_points

        mock_manual_results = init_manual_results(config.scoring_items) if config else {}
        automated_max_score = (
            sum(item.points for item in config.scoring_items if item.item_type == "pytest" and not item.extra_credit)
            if config
            else max_score
        )

        # Generate simulated results for 3 mock students
        mock_students = [
            ("studenta", "11111", "90123", max_score, True, []),
            ("studentb", "22222", "90456", int(max_score * 0.8), True, [{"code": "style_warning", "message": "Line too long"}]),
            ("studentc", "33333", "90789", 0, False, []),
        ]

        student_results = {}
        success_count = 0
        warning_count = 0
        failure_count = 0

        for name, canvas_id, sub_id, score, success, warnings in mock_students:
            if success:
                if warnings:
                    warning_count += 1
                else:
                    success_count += 1
            else:
                failure_count += 1

            student_results[canvas_id] = {
                "student_identifier": name,
                "submission_id": sub_id,
                "bundle_files": ["mock_file.py"],
                "bundle_file_count": 1,
                "success": success,
                "score": score,
                "max_score": max_score,
                "automated_max_score": automated_max_score,
                "test_results": [
                    {"label": "Public behavior checks", "outcome": "passed" if success else "failed", "points_awarded": score, "points": max_score, "passed": success}
                ],
                "warnings": warnings,
                "failure_category": None if success else "missing_required_file",
                "failure_message": None if success else "Required file 'entrypoint.py' is missing.",
                "feedback_html": f"<html><body><h1>Mock Feedback for {name}</h1><p>Score: {score}/{max_score}</p></body></html>",
                "manual_results": {key: dict(item) for key, item in mock_manual_results.items()},
                "overall_comment": "",
            }

        try:
            with retention.access(run_id, db):
                run_dir = official_run_dir(run_id)
                run_dir.mkdir(parents=True, exist_ok=True)

                details_payload = {
                    "unmatched_files": ["unrecognized_export_file.txt"],
                    "student_results": student_results,
                }
                (run_dir / "run_details.json").write_text(json.dumps(details_payload, indent=2))
                write_run_grades_csv(run_dir, student_results)
                write_feedback_zip(run_dir, student_results)

                run.success_count = success_count
                run.warning_count = warning_count
                run.failure_count = failure_count
                run.status = "complete"
                run.failure_summary = {"missing_required_file": 1} if failure_count else {}
                db.commit()

            set_run_state(
                str(run_id),
                "complete",
                {
                    "total": run.total_submission_count,
                    "queued": 0,
                    "running": 0,
                    "completed": success_count + warning_count,
                    "failed": failure_count,
                    "warnings": warning_count,
                    "message": "Official run complete.",
                },
            )
        finally:
            release_execution_slots(owner=f"official:{run_id}")

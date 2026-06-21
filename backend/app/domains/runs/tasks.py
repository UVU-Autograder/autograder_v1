"""Celery tasks for sandbox and official grading runs.

These tasks are dispatched asynchronously and execute the grading pipeline
through Judge0, storing transient results in Redis.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime

from app.integrations.celery.app import celery_app

logger = logging.getLogger(__name__)

# Redis key prefixes for run state
RUN_STATE_PREFIX = "run:state:"
RUN_RESULT_PREFIX = "run:result:"
RUN_STATE_TTL = 3600  # 1 hour


def _get_redis():
    """Get a Redis connection from the Celery broker."""
    import redis
    from app.core.settings import get_settings
    settings = get_settings()
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def set_run_state(run_id: str, state: str, extra: dict | None = None) -> None:
    """Store run state in Redis with TTL."""
    r = _get_redis()
    data = {"state": state, "updated_at": datetime.now(UTC).isoformat()}
    if extra:
        data.update(extra)
    r.setex(f"{RUN_STATE_PREFIX}{run_id}", RUN_STATE_TTL, json.dumps(data))


def get_run_state(run_id: str) -> dict | None:
    """Read run state from Redis."""
    r = _get_redis()
    raw = r.get(f"{RUN_STATE_PREFIX}{run_id}")
    if raw is None:
        return None
    return json.loads(raw)


def set_run_result(run_id: str, result: dict) -> None:
    """Store grading result in Redis with TTL."""
    r = _get_redis()
    r.setex(f"{RUN_RESULT_PREFIX}{run_id}", RUN_STATE_TTL, json.dumps(result))


def get_run_result(run_id: str) -> dict | None:
    """Read grading result from Redis."""
    r = _get_redis()
    raw = r.get(f"{RUN_RESULT_PREFIX}{run_id}")
    if raw is None:
        return None
    return json.loads(raw)


@celery_app.task(
    name="app.domains.runs.tasks.grade_sandbox_run",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def grade_sandbox_run(
    self,
    run_id: str,
    zip_data_b64: str,
    config_json: dict,
    artifact_refs: dict[str, str],
    allowed_concepts: list[str],
) -> dict:
    """Execute a sandbox grading run through the full pipeline.

    This task:
    1. Marks the run as 'run' state in Redis
    2. Decodes the ZIP data
    3. Runs the grading pipeline (AST, Judge0, scoring)
    4. Stores results in Redis
    5. Marks the run as 'complete' or 'failure'

    Args:
        run_id: Unique identifier for this run.
        zip_data_b64: Base64-encoded student submission ZIP.
        config_json: Assignment config as a dict (will be validated).
        artifact_refs: Map of artifact_key -> storage_ref.
        allowed_concepts: Merged effective concept whitelist.

    Returns:
        Dict with grading results summary.
    """
    import base64
    from app.domains.assignments.schemas import AssignmentConfigV1
    from app.domains.grading.service import run_grading_pipeline

    # Mark as running
    set_run_state(run_id, "run")

    try:
        # Decode inputs
        zip_data = base64.b64decode(zip_data_b64)
        config = AssignmentConfigV1.model_validate(config_json)

        # Run the async grading pipeline in a sync context
        loop = asyncio.new_event_loop()
        try:
            grading_result = loop.run_until_complete(
                run_grading_pipeline(
                    zip_data=zip_data,
                    config=config,
                    artifact_refs=artifact_refs,
                    allowed_concepts=allowed_concepts,
                )
            )
        finally:
            loop.close()

        # Build result payload
        result_payload = {
            "run_id": run_id,
            "success": grading_result.success,
            "score": grading_result.score,
            "max_score": grading_result.max_score,
            "test_results": grading_result.test_results,
            "warnings": grading_result.warnings,
            "failure_category": grading_result.failure_category,
            "failure_message": grading_result.failure_message,
        }

        # Store result and update state
        set_run_result(run_id, result_payload)

        if grading_result.success:
            set_run_state(run_id, "complete", {"score": grading_result.score})
        else:
            set_run_state(
                run_id,
                "failure",
                {"failure_category": grading_result.failure_category},
            )

        return result_payload

    except Exception as exc:
        logger.exception("Grading task failed for run %s", run_id)

        error_result = {
            "run_id": run_id,
            "success": False,
            "score": 0,
            "max_score": 0,
            "test_results": [],
            "warnings": [],
            "failure_category": "internal_error",
            "failure_message": f"Internal grading error: {type(exc).__name__}",
        }
        set_run_result(run_id, error_result)
        set_run_state(run_id, "failure", {"failure_category": "internal_error"})

        # Retry with backoff if retries remain
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        return error_result


@celery_app.task(
    name="app.domains.runs.tasks.validate_assignment_model_solution",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def validate_assignment_model_solution(
    self,
    course_code: str,
    assignment_slug: str,
) -> dict:
    """Run model solution against assignment tests in Judge0.

    This task:
    1. Runs preflight checks (AST marker verification, config validation)
    2. Packages model solution into a student ZIP format
    3. Executes grading pipeline
    4. Records validation outcome (success or failure) in Redis
    """
    import base64
    import io
    import zipfile
    from app.db.session import SessionLocal
    from app.domains.assignments.service import get_assignment_for_course, get_artifact_content
    from app.domains.assignments.validation import run_preflight_validation
    from app.domains.assignments.schemas import AssignmentConfigV1
    from app.domains.grading.service import run_grading_pipeline

    run_id = f"val:{course_code}:{assignment_slug}"
    set_run_state(run_id, "run")

    try:
        with SessionLocal() as db:
            # 1. Run preflight validation first
            preflight_errors = run_preflight_validation(db, course_code, assignment_slug)
            if preflight_errors:
                err_payload = {
                    "passed": False,
                    "errors": preflight_errors,
                    "score": 0,
                    "max_score": 0,
                }
                set_run_result(run_id, err_payload)
                set_run_state(run_id, "failure")
                return err_payload

            # Get assignment
            assignment = get_assignment_for_course(db, course_code, assignment_slug)
            config = AssignmentConfigV1.model_validate(assignment.config.config_json)
            max_score = config.base_points

            # 2. Retrieve model solution artifact
            # Find the model_solution artifact key
            model_sol_key = None
            for key, art in config.artifacts.items():
                if art.type == "model_solution":
                    model_sol_key = key
                    break

            if not model_sol_key:
                err_payload = {
                    "passed": False,
                    "errors": ["No 'model_solution' artifact key defined in config."],
                    "score": 0,
                    "max_score": max_score,
                }
                set_run_result(run_id, err_payload)
                set_run_state(run_id, "failure")
                return err_payload

            # Load model solution content
            model_sol_content = get_artifact_content(db, course_code, assignment_slug, model_sol_key)
            if not model_sol_content:
                err_payload = {
                    "passed": False,
                    "errors": [f"Model solution file content is missing or cannot be read for key '{model_sol_key}'."],
                    "score": 0,
                    "max_score": max_score,
                }
                set_run_result(run_id, err_payload)
                set_run_state(run_id, "failure")
                return err_payload

            content_bytes, _ = model_sol_content

            # 3. Package model solution into a student ZIP format matching config entrypoint
            entrypoint = config.bundle.entrypoint
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Add model solution as the entrypoint file
                zip_file.writestr(entrypoint, content_bytes)
                # Also add any required files that might be empty/placeholders
                # to satisfy bundle required_files checks
                for req_file in config.bundle.required_files:
                    if req_file != entrypoint:
                        zip_file.writestr(req_file, b"")

            zip_data = zip_buffer.getvalue()

            # 4. Collect other artifact references
            artifact_refs = {}
            for art in assignment.artifacts:
                # Skip the model_solution itself, but include tests and support files
                if art.artifact_key != model_sol_key and art.storage_ref:
                    artifact_refs[art.artifact_key] = art.storage_ref

            # Merged concepts covered list
            allowed_concepts = list(assignment.course.default_concepts or [])
            if assignment.concept_additions:
                allowed_concepts.extend(assignment.concept_additions.added_concepts or [])

        # 5. Run the grading pipeline asynchronously
        loop = asyncio.new_event_loop()
        try:
            grading_result = loop.run_until_complete(
                run_grading_pipeline(
                    zip_data=zip_data,
                    config=config,
                    artifact_refs=artifact_refs,
                    allowed_concepts=allowed_concepts,
                )
            )
        finally:
            loop.close()

        # 6. Verify success (model solution must score 100% of base points)
        errors = []
        passed = grading_result.success
        if not passed:
            errors.append(f"Grading pipeline failed to run successfully: {grading_result.failure_message}")
        elif grading_result.score < max_score:
            passed = False
            errors.append(
                f"Model solution scored {grading_result.score}/{max_score}. Model solution must score 100%."
            )
            # Find failing test summaries
            for test_res in grading_result.test_results:
                if test_res.get("outcome") != "passed":
                    errors.append(
                        f"Test case '{test_res.get('key')}' failed: {test_res.get('message')}"
                    )

        result_payload = {
            "passed": passed,
            "errors": errors,
            "score": grading_result.score,
            "max_score": max_score,
        }
        set_run_result(run_id, result_payload)

        if passed:
            set_run_state(run_id, "complete")
        else:
            set_run_state(run_id, "failure")

        return result_payload

    except Exception as exc:
        logger.exception("Model solution validation failed for assignment %s", assignment_slug)
        error_result = {
            "passed": False,
            "errors": [f"Internal validation error: {type(exc).__name__}: {str(exc)}"],
            "score": 0,
            "max_score": 0,
        }
        set_run_result(run_id, error_result)
        set_run_state(run_id, "failure")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        return error_result


def generate_pedagogical_feedback_html(student_identifier: str, result: GradingResult) -> str:
    """Generate a clean HTML pedagogical feedback page for the student."""
    tests_html = ""
    for test in result.test_results:
        status_color = "#16a34a" if test.get("passed") else "#dc2626"
        status_text = "PASSED" if test.get("passed") else "FAILED"
        
        # Gather sub test execution details
        sub_tests_html = ""
        sub_tests = test.get("test_results", [])
        if sub_tests:
            sub_tests_html += "<ul style='margin-top: 5px; margin-bottom: 0; padding-left: 20px; font-size: 0.9em; color: #4b5563;'>"
            for sub in sub_tests:
                sub_status = sub.get("outcome", "failed")
                sub_status_color = "#16a34a" if sub_status == "passed" else "#dc2626"
                sub_tests_html += f"<li>{sub.get('nodeid', 'Test Function')} - <strong style='color: {sub_status_color};'>{sub_status.upper()}</strong>"
                if sub.get("message"):
                    sub_tests_html += f"<br/><pre style='font-size: 0.85em; color: #374151; background: #f3f4f6; padding: 5px; border-radius: 3px; overflow-x: auto;'>{sub.get('message')}</pre>"
                sub_tests_html += "</li>"
            sub_tests_html += "</ul>"
            
        tests_html += f"""
        <div style="border: 1px solid #e5e7eb; padding: 15px; margin-bottom: 12px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f3f4f6; padding-bottom: 8px; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 1.1em; color: #1f2937;">{test.get('label', test.get('key', 'Test Case'))}</h3>
                <span style="color: {status_color}; font-weight: bold; font-size: 0.9em; background-color: {status_color}15; padding: 2px 8px; border-radius: 4px;">{status_text}</span>
            </div>
            <p style="margin: 4px 0; font-size: 0.95em; color: #374151;"><strong>Points:</strong> {test.get('points_awarded', 0)} / {test.get('points', 0)}</p>
            {sub_tests_html}
        </div>
        """
        
    warnings_html = ""
    if result.warnings:
        warnings_html += "<h2 style='color: #d97706; border-bottom: 2px solid #fcd34d; padding-bottom: 5px;'>Warnings</h2>"
        for w in result.warnings:
            warnings_html += f"""
            <div style="border-left: 4px solid #f59e0b; background-color: #fffbeb; padding: 12px; margin-bottom: 12px; border-radius: 4px; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">
                <p style="margin: 0; color: #b45309; font-weight: bold;">{w.get('code')}</p>
                <p style="margin: 4px 0 0 0; color: #78350f; font-size: 0.9em;">{w.get('message')}</p>
            </div>
            """
            
    # Include final failure details if run failed overall
    overall_failure_html = ""
    if not result.success and result.failure_message:
        overall_failure_html = f"""
        <div style="border-left: 4px solid #dc2626; background-color: #fef2f2; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
            <h3 style="margin: 0 0 5px 0; color: #991b1b;">Grading Execution Failed</h3>
            <p style="margin: 0; color: #7f1d1d; font-size: 0.95em;"><strong>Category:</strong> {result.failure_category}</p>
            <p style="margin: 5px 0 0 0; color: #7f1d1d; font-size: 0.95em;">{result.failure_message}</p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Autograder Feedback - {student_identifier}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 25px; background-color: #f9fafb; color: #111827; }}
            .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); }}
            h1 {{ margin-top: 0; color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; font-size: 1.75em; }}
            h2 {{ color: #1f2937; font-size: 1.4em; margin-top: 25px; }}
            pre {{ background-color: #f3f4f6; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; border: 1px solid #e5e7eb; }}
            .summary-card {{ background: linear-gradient(135deg, #1f2937, #111827); color: #ffffff; padding: 20px; border-radius: 8px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }}
            .summary-card h2 {{ margin: 0; color: #ffffff; font-size: 1.25em; }}
            .summary-card .score {{ font-size: 2em; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Autograder Feedback</h1>
            <div class="summary-card">
                <div>
                    <h2>Pedagogical Report</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.8; font-size: 0.9em;">Student: {student_identifier}</p>
                </div>
                <div class="score">{result.score} / {result.max_score}</div>
            </div>
            
            {overall_failure_html}
            
            {warnings_html}
            
            <h2 style="border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; margin-bottom: 15px;">Test Cases</h2>
            {tests_html}
        </div>
    </body>
    </html>
    """
    return html


@celery_app.task(
    name="app.domains.runs.tasks.grade_official_run",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def grade_official_run(self, run_id: int) -> dict:
    """Execute official batch grading run asynchronously."""
    import shutil
    import csv
    import zipfile
    from pathlib import Path
    import io
    import asyncio
    import json
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.db.session import SessionLocal
    from app.domains.runs.models import RunSummary
    from app.domains.assignments.models import Assignment
    from app.domains.assignments.schemas import AssignmentConfigV1
    from app.domains.ingestion.extractor import (
        safe_extract_zip,
        group_canvas_files,
        prepare_student_bundle,
        parse_canvas_filename,
    )
    from app.domains.grading.service import run_grading_pipeline, GradingResult
    from app.core.settings import get_settings

    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    zip_path = workspaces_dir / f"official_{run_id}.zip"

    with SessionLocal() as db:
        run = db.scalar(select(RunSummary).where(RunSummary.id == run_id))
        if not run:
            logger.error("RunSummary %d not found.", run_id)
            return {"error": "RunSummary not found"}

        run.status = "run"
        db.commit()

        assignment = db.scalar(
            select(Assignment)
            .where(Assignment.id == run.assignment_id)
            .options(
                selectinload(Assignment.course),
                selectinload(Assignment.config),
                selectinload(Assignment.artifacts),
            )
        )
        if not assignment or not assignment.config:
            logger.error("Assignment or config not found for run %d", run_id)
            run.status = "failure"
            db.commit()
            return {"error": "Assignment or config not found"}

        config = AssignmentConfigV1.model_validate(assignment.config.config_json)
        max_score = config.base_points

        # Build artifact references
        artifact_refs = {}
        for art in assignment.artifacts:
            if art.storage_ref:
                artifact_refs[art.artifact_key] = art.storage_ref

        # Merged concepts covered list
        allowed_concepts = list(assignment.course.default_concepts or [])
        if assignment.concept_additions:
            allowed_concepts.extend(assignment.concept_additions.added_concepts or [])

    if not zip_path.exists():
        logger.error("ZIP path %s not found.", zip_path)
        with SessionLocal() as db:
            run_db = db.scalar(select(RunSummary).where(RunSummary.id == run_id))
            if run_db:
                run_db.status = "failure"
                db.commit()
        return {"error": "Official ZIP not found"}

    run_dir = workspaces_dir / f"official_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = run_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        safe_extract_zip(zip_path.read_bytes(), extract_dir)
    except Exception as e:
        logger.exception("Failed to extract official ZIP: %s", e)
        with SessionLocal() as db:
            run_db = db.scalar(select(RunSummary).where(RunSummary.id == run_id))
            if run_db:
                run_db.status = "failure"
                run_db.failure_summary = {"extraction_error": str(e)}
                db.commit()
        return {"error": "Failed to extract ZIP"}

    grouped_files, unmatched = group_canvas_files(extract_dir)

    student_results = {}
    success_count = 0
    warning_count = 0
    failure_count = 0
    timeout_count = 0
    failure_summary_counts = {}

    for canvas_user_id, paths in grouped_files.items():
        student_identifier = "unknown"
        submission_id = "unknown"
        for p in paths:
            parsed = parse_canvas_filename(p.name)
            if parsed:
                student_identifier, _, submission_id, _ = parsed
                break

        student_temp_dir = run_dir / f"student_{canvas_user_id}"
        student_temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            prepare_student_bundle(paths, student_temp_dir)
        except Exception as e:
            failure_count += 1
            failure_summary_counts["preparation_error"] = failure_summary_counts.get("preparation_error", 0) + 1
            student_results[canvas_user_id] = {
                "student_identifier": student_identifier,
                "submission_id": submission_id,
                "success": False,
                "score": 0,
                "max_score": max_score,
                "test_results": [],
                "warnings": [],
                "failure_category": "preparation_error",
                "failure_message": f"Failed to prepare submission bundle: {str(e)}",
                "feedback_html": f"<html><body><p>Error preparing submission: {str(e)}</p></body></html>"
            }
            continue

        student_zip_buffer = io.BytesIO()
        with zipfile.ZipFile(student_zip_buffer, "w", zipfile.ZIP_DEFLATED) as sz:
            for filepath in student_temp_dir.rglob("*"):
                if filepath.is_file():
                    sz.write(filepath, filepath.relative_to(student_temp_dir))
        student_zip_bytes = student_zip_buffer.getvalue()

        loop = asyncio.new_event_loop()
        try:
            grading_result = loop.run_until_complete(
                run_grading_pipeline(
                    zip_data=student_zip_bytes,
                    config=config,
                    artifact_refs=artifact_refs,
                    allowed_concepts=allowed_concepts,
                )
            )
        except Exception as exc:
            logger.exception("Grading pipeline crashed for student %s", student_identifier)
            grading_result = GradingResult(
                success=False,
                failure_category="internal_error",
                failure_message=f"Grading error: {type(exc).__name__}",
                max_score=max_score
            )
        finally:
            loop.close()

        feedback_html = generate_pedagogical_feedback_html(student_identifier, grading_result)

        if grading_result.success:
            if grading_result.warnings:
                warning_count += 1
            else:
                success_count += 1
        else:
            if grading_result.failure_category == "timeout":
                timeout_count += 1
            else:
                failure_count += 1
            cat = grading_result.failure_category or "unknown_failure"
            failure_summary_counts[cat] = failure_summary_counts.get(cat, 0) + 1

        student_results[canvas_user_id] = {
            "student_identifier": student_identifier,
            "submission_id": submission_id,
            "success": grading_result.success,
            "score": grading_result.score,
            "max_score": grading_result.max_score,
            "test_results": grading_result.test_results,
            "warnings": [dict(w) for w in grading_result.warnings],
            "failure_category": grading_result.failure_category,
            "failure_message": grading_result.failure_message,
            "feedback_html": feedback_html
        }

        shutil.rmtree(student_temp_dir, ignore_errors=True)

        with SessionLocal() as db:
            run_db = db.scalar(select(RunSummary).where(RunSummary.id == run_id))
            if run_db:
                run_db.success_count = success_count
                run_db.warning_count = warning_count
                run_db.failure_count = failure_count
                run_db.timeout_count = timeout_count
                run_db.failure_summary = failure_summary_counts
                db.commit()

    # Clean up extraction workspace directory
    shutil.rmtree(extract_dir, ignore_errors=True)

    # Save details, CSV and feedback packages
    details_payload = {
        "unmatched_files": [p.name for p in unmatched],
        "student_results": student_results
    }
    (run_dir / "run_details.json").write_text(json.dumps(details_payload, indent=2))

    csv_path = run_dir / "grades.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Student Identifier", "Canvas User ID", "Submission ID", "Score", "Max Score"])
        for canvas_user_id, res in student_results.items():
            writer.writerow([
                res["student_identifier"],
                canvas_user_id,
                res["submission_id"],
                res["score"],
                res["max_score"]
            ])

    zip_export_path = run_dir / "feedback.zip"
    with zipfile.ZipFile(zip_export_path, "w", zipfile.ZIP_DEFLATED) as z_out:
        for canvas_user_id, res in student_results.items():
            filename = f"{res['student_identifier']}_{canvas_user_id}_feedback.html"
            z_out.writestr(filename, res["feedback_html"])

    with SessionLocal() as db:
        run_db = db.scalar(select(RunSummary).where(RunSummary.id == run_id))
        if run_db:
            run_db.status = "complete"
            db.commit()

    return details_payload


def run_mock_official_run(run_id: int) -> None:
    """Synchronously populate mock database results and ephemeral files for offline testing."""
    import json
    import csv
    import zipfile
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.domains.runs.models import RunSummary
    from app.domains.assignments.models import Assignment
    from app.domains.assignments.schemas import AssignmentConfigV1
    from app.core.settings import get_settings

    with SessionLocal() as db:
        run = db.scalar(select(RunSummary).where(RunSummary.id == run_id))
        if not run:
            return

        run.status = "run"
        db.commit()

        assignment = db.scalar(select(Assignment).where(Assignment.id == run.assignment_id))
        max_score = 100
        if assignment and assignment.config:
            try:
                config = AssignmentConfigV1.model_validate(assignment.config.config_json)
                max_score = config.base_points
            except Exception:
                pass

        # Generate simulated results for 3 mock students
        mock_students = [
            ("studenta", "11111", "90123", max_score, True, []),
            ("studentb", "22222", "90456", int(max_score * 0.8), True, [{"code": "style_warning", "message": "Line too long"}]),
            ("studentc", "33333", "90789", 0, False, [])
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
                "success": success,
                "score": score,
                "max_score": max_score,
                "test_results": [
                    {"label": "Public behavior checks", "outcome": "passed" if success else "failed", "points_awarded": score, "points": max_score, "passed": success}
                ],
                "warnings": warnings,
                "failure_category": None if success else "missing_required_file",
                "failure_message": None if success else "Required file 'entrypoint.py' is missing.",
                "feedback_html": f"<html><body><h1>Mock Feedback for {name}</h1><p>Score: {score}/{max_score}</p></body></html>"
            }

        settings = get_settings()
        workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
        run_dir = workspaces_dir / f"official_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save mock files
        details_payload = {
            "unmatched_files": ["unrecognized_export_file.txt"],
            "student_results": student_results
        }
        (run_dir / "run_details.json").write_text(json.dumps(details_payload, indent=2))

        with open(run_dir / "grades.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Student Identifier", "Canvas User ID", "Submission ID", "Score", "Max Score"])
            for canvas_id, res in student_results.items():
                writer.writerow([res["student_identifier"], canvas_id, res["submission_id"], res["score"], res["max_score"]])

        with zipfile.ZipFile(run_dir / "feedback.zip", "w", zipfile.ZIP_DEFLATED) as z_out:
            for canvas_id, res in student_results.items():
                z_out.writestr(f"{res['student_identifier']}_{canvas_id}_feedback.html", res["feedback_html"])

        run.success_count = success_count
        run.warning_count = warning_count
        run.failure_count = failure_count
        run.status = "complete"
        run.failure_summary = {"missing_required_file": 1} if failure_count else {}
        db.commit()


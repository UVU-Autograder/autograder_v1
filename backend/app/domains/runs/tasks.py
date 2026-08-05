"""Celery tasks for sandbox and official grading runs.

These tasks are dispatched asynchronously and execute the grading pipeline
through Judge0, storing transient results in Redis.
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
import zipfile
from datetime import UTC, datetime

from app.db.base import import_domain_models
import_domain_models()

from app.integrations.celery.app import celery_app

from app.domains.runs.lifecycle import RunLifecycleTracker
from app.domains.runs.queue_admission import release_execution_slots, reserve_execution_slots
from app.domains.runs.feedback_formatter import generate_pedagogical_feedback_html
from app.domains.runs.mock_runner import run_mock_official_run
from app.domains.runs.orchestrator import (
    RUN_CANCELLED_PREFIX,
    RUN_RESULT_PREFIX,
    RUN_STATE_PREFIX,
    RUN_STATE_TTL,
    _get_redis,
    build_model_solution_zip,
    execute_sandbox_run,
    failing_automated_items,
    get_run_result,
    get_run_state,
    is_run_cancelled,
    mark_run_cancelled,
    set_run_result,
    set_run_state,
)

logger = logging.getLogger(__name__)


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
    stdin: str | None = None,
) -> dict:
    """Execute a sandbox grading run through the orchestrator pipeline."""
    return execute_sandbox_run(
        run_id=run_id,
        zip_data_b64=zip_data_b64,
        config_json=config_json,
        artifact_refs=artifact_refs,
        allowed_concepts=allowed_concepts,
        stdin=stdin,
    )




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
    from app.db.session import SessionLocal
    from app.domains.assignments.service import get_assignment_for_course, get_artifact_content
    from app.domains.assignments.validation import run_preflight_validation
    from app.domains.assignments.schemas import AssignmentConfigV1
    from app.domains.grading.engine import GradingEngine

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
            if not assignment or not assignment.config:
                raise ValueError("Assignment config not found.")
            config = AssignmentConfigV1.model_validate(assignment.config.config_json)
            max_score = sum(
                item.points for item in config.tests if not item.extra_credit
            )

            # 2. Retrieve every file in the instructor model bundle.
            model_artifacts = {
                key: artifact
                for key, artifact in config.artifacts.items()
                if artifact.type == "model_solution"
            }
            if not model_artifacts:
                err_payload = {
                    "passed": False,
                    "errors": ["No 'model_solution' artifacts defined in config."],
                    "score": 0,
                    "max_score": max_score,
                }
                set_run_result(run_id, err_payload)
                set_run_state(run_id, "failure")
                return err_payload

            model_files: dict[str, bytes] = {}
            model_keys: set[str] = set()
            for key, artifact in model_artifacts.items():
                if not artifact.display_filename:
                    raise ValueError(
                        f"Model solution artifact '{key}' is missing display_filename."
                    )
                if artifact.display_filename in model_files:
                    raise ValueError(
                        "Duplicate model solution filename: "
                        f"{artifact.display_filename}"
                    )
                content = get_artifact_content(
                    db, course_code, assignment_slug, key
                )
                if not content:
                    raise ValueError(
                        "Model solution file content is missing or cannot be read "
                        f"for key '{key}'."
                    )
                model_files[artifact.display_filename] = content[0]
                model_keys.add(key)

            # 3. Package only real instructor files; required paths may not be empty.
            zip_data = build_model_solution_zip(
                config.bundle.required_files,
                model_files,
            )

            # 4. Collect other artifact references
            artifact_refs = {}
            for art in assignment.artifacts:
                # Model files are student-bundle inputs, never grading support.
                if art.artifact_key not in model_keys and art.storage_ref:
                    artifact_refs[art.artifact_key] = art.storage_ref

            # Merged concepts covered list
            from app.domains.assignments.service import effective_allowed_concepts

            allowed_concepts = effective_allowed_concepts(assignment)

        # 5. Run the grading engine asynchronously (with execution slot tracking)
        if not reserve_execution_slots(1):
            err_payload = {
                "passed": False,
                "errors": ["Queue full. Model solution validation cannot execute currently."],
                "score": 0,
                "max_score": max_score,
            }
            set_run_result(run_id, err_payload)
            set_run_state(run_id, "failure")
            return err_payload

        try:
            engine = GradingEngine(
                config=config,
                artifact_refs=artifact_refs,
                allowed_concepts=allowed_concepts,
            )
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                grading_result = loop.run_until_complete(
                    engine.grade_submission(zip_data=zip_data)
                )
            finally:
                asyncio.set_event_loop(None)
                loop.close()
        finally:
            release_execution_slots(1)

        # 6. Every automated item must pass; manual rubric items are excluded.
        errors = []
        passed = grading_result.success
        if not passed:
            errors.append(f"Grading pipeline failed to run successfully: {grading_result.failure_message}")
        failing_tests = failing_automated_items(grading_result.test_results)
        if passed and failing_tests:
            passed = False
            errors.append(
                "Model solution must pass every automated scoring item."
            )
            for test_res in failing_tests:
                errors.append(
                    f"Test case '{test_res.get('key')}' failed: "
                    f"{test_res.get('message')}"
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
    from app.domains.grading.engine import GradingEngine, GradingResult
    from app.core.settings import get_settings
    from app.domains.runs.service import (
        init_manual_results,
        official_run_dir,
        official_run_zip_path,
        write_feedback_zip,
        write_run_grades_csv,
    )
    settings = get_settings()
    zip_path = official_run_zip_path(run_id)

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
            release_execution_slots(run.total_submission_count or 0)
            set_run_state(str(run_id), "failure", {"message": "Assignment or config not found"})
            return {"error": "Assignment or config not found"}

        config = AssignmentConfigV1.model_validate(assignment.config.config_json)
        max_score = config.base_points
        automated_max_score = sum(
            item.points for item in config.scoring_items if item.item_type == "pytest" and not item.extra_credit
        )
        total_submissions = run.total_submission_count

        # Build artifact references
        artifact_refs = {}
        for art in assignment.artifacts:
            if art.storage_ref:
                artifact_refs[art.artifact_key] = art.storage_ref

        # Merged concepts covered list
        from app.domains.assignments.service import effective_allowed_concepts

        allowed_concepts = effective_allowed_concepts(assignment)
        grading_engine = GradingEngine(
            config=config,
            artifact_refs=artifact_refs,
            allowed_concepts=allowed_concepts,
        )

    tracker = RunLifecycleTracker(run_id, total_submissions)
    tracker.set_running("Official run executing.")

    if not zip_path.exists():
        logger.error("ZIP path %s not found.", zip_path)
        tracker.mark_failure("Official ZIP not found", "zip_not_found")
        tracker.release_remaining_slots()
        return {"error": "Official ZIP not found"}

    run_dir = official_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = run_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        safe_extract_zip(zip_path.read_bytes(), extract_dir)
    except Exception as e:
        logger.exception("Failed to extract official ZIP: %s", e)
        tracker.mark_failure("Failed to extract ZIP", type(e).__name__)
        tracker.release_remaining_slots()
        return {"error": "Failed to extract ZIP"}

    try:
        grouped_files, unmatched = group_canvas_files(extract_dir)

        unused_slots = max(0, total_submissions - len(grouped_files))
        if unused_slots:
            tracker.release_slots(unused_slots)

        student_results = {}
        success_count = 0
        warning_count = 0
        failure_count = 0
        timeout_count = 0
        failure_summary_counts = {}

        async def grade_student_async(canvas_user_id: str, paths: list[Path], semaphore: asyncio.Semaphore):
            nonlocal success_count, warning_count, failure_count, timeout_count

            student_identifier = "unknown"
            submission_id = "unknown"
            original_filename = "unknown"
            for p in paths:
                parsed = parse_canvas_filename(p.name)
                if parsed:
                    student_identifier, _, submission_id, original_filename = parsed
                    break

            student_temp_dir = run_dir / f"student_{canvas_user_id}"
            student_temp_dir.mkdir(parents=True, exist_ok=True)
            manual_results = init_manual_results(config.scoring_items)

            try:
                prepare_student_bundle(paths, student_temp_dir)
            except Exception as e:
                failure_count += 1
                failure_summary_counts["preparation_error"] = failure_summary_counts.get("preparation_error", 0) + 1
                student_results[canvas_user_id] = {
                    "student_identifier": student_identifier,
                    "submission_id": submission_id,
                    "matched_file": original_filename,
                    "success": False,
                    "score": 0,
                    "max_score": max_score,
                    "automated_max_score": automated_max_score,
                    "test_results": [],
                    "warnings": [],
                    "failure_category": "preparation_error",
                    "failure_message": f"Failed to prepare submission bundle: {str(e)}",
                    "feedback_html": f"<html><body><p>Error preparing submission: {str(e)}</p></body></html>",
                    "manual_results": manual_results,
                    "overall_comment": "",
                }
                shutil.rmtree(student_temp_dir, ignore_errors=True)
                tracker.release_slots(1)
                tracker.update_progress(success_count, warning_count, failure_count, timeout_count, failure_summary_counts)
                return

            student_zip_buffer = io.BytesIO()
            with zipfile.ZipFile(student_zip_buffer, "w", zipfile.ZIP_DEFLATED) as sz:
                for filepath in student_temp_dir.rglob("*"):
                    if filepath.is_file():
                        sz.write(filepath, filepath.relative_to(student_temp_dir))
            student_zip_bytes = student_zip_buffer.getvalue()

            try:
                try:
                    async with semaphore:
                        grading_result = await grading_engine.grade_submission(
                            zip_data=student_zip_bytes,
                        )
                except Exception as exc:
                    logger.exception("Grading pipeline crashed during student submission execution")
                    grading_result = GradingResult(
                        success=False,
                        failure_category="internal_error",
                        failure_message=f"Grading error: {type(exc).__name__}",
                        max_score=max_score
                    )

                feedback_html = generate_pedagogical_feedback_html(student_identifier, grading_result, manual_results)

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
                    "matched_file": original_filename,
                    "success": grading_result.success,
                    "score": grading_result.score,
                    "max_score": grading_result.max_score,
                    "automated_max_score": automated_max_score,
                    "test_results": grading_result.test_results,
                    "warnings": [dict(w) for w in grading_result.warnings],
                    "failure_category": grading_result.failure_category,
                    "failure_message": grading_result.failure_message,
                    "feedback_html": feedback_html,
                    "manual_results": manual_results,
                    "overall_comment": "",
                }

                tracker.update_progress(success_count, warning_count, failure_count, timeout_count, failure_summary_counts)
            finally:
                tracker.release_slots(1)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            semaphore = asyncio.Semaphore(settings.judge0_max_concurrent)
            tasks = [
                grade_student_async(canvas_user_id, paths, semaphore)
                for canvas_user_id, paths in grouped_files.items()
            ]
            loop.run_until_complete(asyncio.gather(*tasks))
        finally:
            asyncio.set_event_loop(None)
            loop.close()

        # Clean up extraction workspace directory
        shutil.rmtree(extract_dir, ignore_errors=True)

        # Save details, CSV and feedback packages
        details_payload = {
            "unmatched_files": [p.name for p in unmatched],
            "student_results": student_results
        }
        (run_dir / "run_details.json").write_text(json.dumps(details_payload, indent=2))
        write_run_grades_csv(run_dir, student_results)
        write_feedback_zip(run_dir, student_results)

        tracker.mark_complete(success_count, warning_count, failure_count + timeout_count, failure_summary_counts)
        return details_payload
    finally:
        tracker.release_remaining_slots()


@celery_app.task(name="app.domains.runs.tasks.cleanup_expired_workspaces")
def cleanup_expired_workspaces() -> dict:
    """Clean up workspaces and ZIP files for runs older than 24 hours."""
    from datetime import datetime, timedelta, UTC
    import shutil
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.domains.runs.models import RunSummary
    from app.domains.runs.service import (
        official_run_dir,
        official_run_zip_path,
    )

    cutoff = datetime.now(UTC) - timedelta(hours=24)

    cleaned_count = 0
    errors = []

    with SessionLocal() as db:
        # Select official runs older than 24 hours
        stmt = select(RunSummary).where(
            RunSummary.created_at < cutoff,
            RunSummary.workflow_type == "official",
        )
        old_runs = db.scalars(stmt).all()

        for run in old_runs:
            run_dir = official_run_dir(run.id)
            zip_file = official_run_zip_path(run.id)
            deleted_any = False

            if run_dir.exists():
                try:
                    shutil.rmtree(run_dir, ignore_errors=True)
                    deleted_any = True
                except Exception as e:
                    errors.append(f"Failed to remove run_dir {run.id}: {str(e)}")

            if zip_file.exists():
                try:
                    zip_file.unlink(missing_ok=True)
                    deleted_any = True
                except Exception as e:
                    errors.append(f"Failed to unlink ZIP {run.id}: {str(e)}")

            if deleted_any:
                cleaned_count += 1

    return {"cleaned_runs_count": cleaned_count, "errors": errors}


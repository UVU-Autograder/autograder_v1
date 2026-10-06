"""Celery tasks for sandbox and official grading runs.

These tasks are dispatched asynchronously and execute the grading pipeline
through Judge0. Sandbox/model-validation results use transient Redis state;
official review data stays in the governed workspace and official task results
are ignored by Celery.
"""
from __future__ import annotations

import asyncio
import logging
from celery.exceptions import Retry

from fastapi import HTTPException

from app.db.base import import_domain_models

import_domain_models()

from app.domains.runs.mock_runner import run_mock_official_run
from app.domains.runs.orchestrator import (
    build_model_solution_zip,
    execute_sandbox_run,
    failing_automated_items,
    get_run_result,
    get_run_state,
    set_run_result,
    set_run_state,
)

__all__ = [
    "get_run_state",
    "get_run_result",
    "run_mock_official_run",
    "grade_official_run",
    "grade_sandbox_run",
    "validate_assignment_model_solution",
    "cleanup_expired_workspaces",
]
from app.domains.runs.queue_admission import (
    release_execution_slots,
    reserve_execution_slots,
)
from app.integrations.celery.app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.domains.runs.tasks.grade_sandbox_run",
    bind=True,
    max_retries=None,
    soft_time_limit=120,
    time_limit=180,
    default_retry_delay=5,
    acks_late=True,
)
def grade_sandbox_run(
    self,
    run_id: str,
    zip_data_b64: str,
    config: dict,
    artifact_refs: dict[str, str],
    allowed_concepts: list[str],
    stdin: str | None = None,
) -> dict:
    """Execute a sandbox grading run through the orchestrator pipeline."""
    from app.domains.runs.queue_admission import claim, QueueFullError
    try:
        token = claim(run_id)
    except QueueFullError:
        raise self.retry(countdown=2, max_retries=None)
    if token is None:
        return {"run_id": run_id, "state": "ignored"}
    return execute_sandbox_run(
        run_id=run_id,
        zip_data_b64=zip_data_b64,
        config=config,
        artifact_refs=artifact_refs,
        allowed_concepts=allowed_concepts,
        stdin=stdin,
    )




@celery_app.task(
    name="app.domains.runs.tasks.validate_assignment_model_solution",
    bind=True,
    max_retries=3,
    soft_time_limit=120,
    time_limit=180,
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
    from app.domains.assignments.schemas import AssignmentConfigV1
    from app.domains.assignments.service import (
        get_artifact_content,
        get_assignment_for_course,
    )
    from app.domains.assignments.validation import run_preflight_validation
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
            config = AssignmentConfigV1.model_validate(assignment.config.config)
            max_score = sum(
                item.points
                for item in config.scoring_items
                if item.item_type == "pytest" and not item.extra_credit
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
                config.bundle.derived_required_files(),
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
        from uuid import uuid4
        from app.domains.runs.queue_admission import claim, QueueFullError
        owner = f"validation:{self.request.id or uuid4()}"
        if not reserve_execution_slots(1, owner=owner):
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
            token = claim(owner)
        except QueueFullError:
            raise self.retry(countdown=2, max_retries=1800)
        if token is None:
            return {"passed": False, "errors": ["Execution attempt unavailable."], "score": 0, "max_score": max_score}
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
            release_execution_slots(owner=owner)

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

    except Retry:
        raise
    except Exception as exc:
        logger.exception("Model solution validation failed for assignment %s", assignment_slug)
        error_result = {
            "passed": False,
            "errors": [f"Internal validation error: {type(exc).__name__}: {exc!s}"],
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
    max_retries=None,
    soft_time_limit=120,
    time_limit=180,
    default_retry_delay=5,
    acks_late=True,
    ignore_result=True,
    store_errors_even_if_ignored=False,
)
def grade_official_run(self, run_id: int, token: str | None = None) -> dict:
    """Execute one checkpointed submission. Dispatcher owns retry/recovery."""
    from app.db.session import SessionLocal
    from app.domains.runs.models import RunSummary
    from app.domains.runs.official_execution import step
    from app.domains.runs.dispatcher import finish_step
    from app.domains.runs.queue_admission import claim, QueueFullError

    if token is None:
        # Legacy broker deliveries must never start an unbounded batch.
        return {"run_id": run_id, "state": "ignored"}
    try:
        claimed = claim(f"official:{run_id}", token)
    except QueueFullError:
        raise self.retry(countdown=2, max_retries=None)
    if not claimed:
        return {"run_id": run_id, "state": "ignored"}
    try:
        outcome = step(run_id, token)
    except HTTPException as exc:
        if exc.status_code == 410:
            with SessionLocal() as db:
                run = db.get(RunSummary, run_id)
                if run:
                    run.status = "failure"
                    run.failure_summary = {"error": "review_expired"}
                    db.commit()
            finish_step(run_id, token)
        return {"run_id": run_id, "state": "failure", "failure_category":
                "review_expired" if exc.status_code == 410 else "execution_unavailable"}
    except Exception:
        # Keep the lease: dispatcher retries with a fresh generation after the
        # hard-limit/remote-execution safety window, then fails after 3 attempts.
        logger.error("Official execution attempt interrupted")
        return {"run_id": run_id, "state": "failure", "failure_category": "execution_interrupted"}
    finish_step(run_id, token)
    return outcome


def cleanup_expired_workspaces() -> dict:
    """Compatibility entry point; scheduling belongs to the dedicated service."""
    from app.db.session import SessionLocal
    from app.domains.runs import retention

    with SessionLocal() as db:
        return retention.reconcile(db)

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

"""Run Execution Orchestrator.

Decouples run lifecycle orchestration, Redis state management, Judge0 execution,
and result persistence from Celery task worker wrappers.
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import zipfile
from datetime import UTC, datetime

import redis

from app.core.settings import get_settings
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.service import run_grading_pipeline
from app.domains.runs.queue_admission import release_execution_slots


logger = logging.getLogger(__name__)

# Redis key prefixes for run state
RUN_STATE_PREFIX = "run:state:"
RUN_RESULT_PREFIX = "run:result:"
RUN_CANCELLED_PREFIX = "run:cancelled:"
RUN_STATE_TTL = 3600  # 1 hour


def build_model_solution_zip(
    required_files: list[str],
    model_files: dict[str, bytes],
) -> bytes:
    """Build a complete model bundle without synthetic placeholder files."""
    missing = [path for path in required_files if path not in model_files]
    if missing:
        raise ValueError(
            "Missing model solution artifacts for required files: "
            + ", ".join(sorted(missing))
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename, content in model_files.items():
            archive.writestr(filename, content)
    return buffer.getvalue()


def failing_automated_items(test_results: list[dict]) -> list[dict]:
    """Return scored items that did not explicitly pass."""
    return [
        result for result in test_results if result.get("passed") is not True
    ]


def _get_redis():
    """Get a Redis connection from the Celery broker."""
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


def mark_run_cancelled(run_id: str) -> None:
    """Durable cancel marker so workers skip release after cancel_run."""
    r = _get_redis()
    r.setex(f"{RUN_CANCELLED_PREFIX}{run_id}", RUN_STATE_TTL, "1")


def is_run_cancelled(run_id: str) -> bool:
    try:
        return bool(_get_redis().get(f"{RUN_CANCELLED_PREFIX}{run_id}"))
    except Exception:
        state = get_run_state(run_id) or {}
        return state.get("failure_category") == "cancelled"


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


def execute_sandbox_run(
    run_id: str,
    zip_data_b64: str,
    config_json: dict,
    artifact_refs: dict[str, str],
    allowed_concepts: list[str],
    stdin: str | None = None,
) -> dict:
    """Execute a sandbox grading run directly through the pipeline."""
    if is_run_cancelled(run_id):
        return {
            "run_id": run_id,
            "success": False,
            "score": 0,
            "max_score": 0,
            "test_results": [],
            "warnings": [],
            "failure_category": "cancelled",
            "failure_message": "Sandbox run was cancelled before execution.",
        }

    set_run_state(run_id, "run")
    if is_run_cancelled(run_id):
        return {
            "run_id": run_id,
            "success": False,
            "score": 0,
            "max_score": 0,
            "test_results": [],
            "warnings": [],
            "failure_category": "cancelled",
            "failure_message": "Sandbox run was cancelled before execution.",
        }

    try:
        zip_data = base64.b64decode(zip_data_b64)
        config = AssignmentConfigV1.model_validate(config_json)

        loop = asyncio.new_event_loop()
        try:
            grading_result = loop.run_until_complete(
                run_grading_pipeline(
                    zip_data=zip_data,
                    config=config,
                    artifact_refs=artifact_refs,
                    allowed_concepts=allowed_concepts,
                    stdin=stdin,
                )
            )
        finally:
            loop.close()

        if is_run_cancelled(run_id):
            return {
                "run_id": run_id,
                "success": False,
                "score": 0,
                "max_score": 0,
                "test_results": [],
                "warnings": [],
                "failure_category": "cancelled",
                "failure_message": "Sandbox run was cancelled after pipeline execution.",
            }

        result_dict = {
            "run_id": run_id,
            "success": grading_result.success,
            "score": grading_result.score,
            "max_score": grading_result.max_score,
            "test_results": grading_result.test_results,
            "warnings": grading_result.warnings,
            "failure_category": grading_result.failure_category,
            "failure_message": grading_result.failure_message,
        }

        set_run_result(run_id, result_dict)
        if grading_result.success:
            set_run_state(run_id, "complete")
        else:
            set_run_state(
                run_id,
                "failure",
                extra={
                    "failure_category": grading_result.failure_category or "unknown",
                    "failure_message": grading_result.failure_message or "Execution failed.",
                },
            )

        return result_dict

    except Exception as exc:
        logger.exception("Unexpected error in sandbox run %s", run_id)
        failure_dict = {
            "run_id": run_id,
            "success": False,
            "score": 0,
            "max_score": 0,
            "test_results": [],
            "warnings": [],
            "failure_category": "internal_error",
            "failure_message": f"Pipeline error: {exc!s}",
        }
        set_run_result(run_id, failure_dict)
        set_run_state(
            run_id,
            "failure",
            extra={
                "failure_category": "internal_error",
                "failure_message": str(exc),
            },
        )
        return failure_dict
    finally:
        if not is_run_cancelled(run_id):
            try:
                release_execution_slots(1)
            except Exception as rel_err:
                logger.warning("Failed releasing sandbox slot for %s: %s", run_id, rel_err)


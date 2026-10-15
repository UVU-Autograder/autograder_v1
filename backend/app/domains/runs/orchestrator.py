"""Run Execution Orchestrator.

Decouples run lifecycle orchestration, Redis state management, Judge0 execution,
and result persistence from Celery task worker wrappers.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import time
import zipfile
from datetime import UTC, datetime

import redis

from app.core.audit_log import audit_context
from app.core.settings import get_settings
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.runs.queue_admission import release_execution_slots

logger = logging.getLogger(__name__)

# Redis key prefixes for run state
RUN_STATE_PREFIX = "run:state:"
RUN_RESULT_PREFIX = "run:result:"
RUN_CANCELLED_PREFIX = "run:cancelled:"
RUN_STATE_TTL = 3600  # 1 hour
# Rolling window of recent sandbox grading durations (seconds only; no run ids),
# used to turn "N submissions ahead" into a wait estimate.
GRADE_SECONDS_KEY = "sandbox:grade_seconds"
GRADE_SECONDS_WINDOW = 50
DEFAULT_GRADE_SECONDS = 10.0
# When recent gradings finished (epoch seconds only). Observed throughput includes
# every real-world overhead -- claim retries, a single Judge0 worker -- that the
# ideal "slots x mean time" estimate misses.
COMPLETIONS_KEY = "sandbox:completions"
THROUGHPUT_WINDOW_SECONDS = 180
MIN_COMPLETIONS_FOR_THROUGHPUT = 4


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
    """Return automated scored items that did not explicitly pass.

    Manual rubric items have no pytest to run, so they never report passed=True;
    they are staff-graded and must not count as automated failures. Results with
    no item_type are treated as automated.
    """
    return [
        result
        for result in test_results
        if result.get("item_type", "pytest") != "manual" and result.get("passed") is not True
    ]


_local_state_cache: dict[str, dict] = {}
_local_result_cache: dict[str, dict] = {}
_local_cancelled_set: set[str] = set()
_local_grade_seconds: list[float] = []
_local_completions: list[float] = []


def clear_local_orchestrator_cache() -> None:
    _local_state_cache.clear()
    _local_result_cache.clear()
    _local_cancelled_set.clear()
    _local_grade_seconds.clear()
    _local_completions.clear()


def record_grade_seconds(seconds: float) -> None:
    """Remember how long one sandbox grading took (aggregate timing only)."""
    if seconds <= 0:
        return
    finished = time.time()
    _local_grade_seconds.insert(0, seconds)
    del _local_grade_seconds[GRADE_SECONDS_WINDOW:]
    _local_completions.insert(0, finished)
    del _local_completions[GRADE_SECONDS_WINDOW:]
    try:
        r = _get_redis()
        r.lpush(GRADE_SECONDS_KEY, f"{seconds:.3f}")
        r.ltrim(GRADE_SECONDS_KEY, 0, GRADE_SECONDS_WINDOW - 1)
        r.lpush(COMPLETIONS_KEY, f"{finished:.3f}")
        r.ltrim(COMPLETIONS_KEY, 0, GRADE_SECONDS_WINDOW - 1)
    except Exception:
        pass


def recent_throughput_per_second() -> float | None:
    """Gradings finished per second over the last few minutes, if there were enough of them."""
    try:
        r = _get_redis()
        stamps = [float(v) for v in r.lrange(COMPLETIONS_KEY, 0, GRADE_SECONDS_WINDOW - 1)]
    except Exception:
        stamps = list(_local_completions)
    cutoff = time.time() - THROUGHPUT_WINDOW_SECONDS
    recent = [t for t in stamps if t >= cutoff]
    if len(recent) < MIN_COMPLETIONS_FOR_THROUGHPUT:
        return None
    span = max(recent) - min(recent)
    return (len(recent) - 1) / span if span > 0 else None


def mean_grade_seconds() -> float:
    """Mean of recent sandbox grading durations, or a default before any run finished."""
    values: list[float] = []
    try:
        r = _get_redis()
        values = [float(v) for v in r.lrange(GRADE_SECONDS_KEY, 0, GRADE_SECONDS_WINDOW - 1)]
    except Exception:
        values = list(_local_grade_seconds)
    return sum(values) / len(values) if values else DEFAULT_GRADE_SECONDS


def _get_redis():
    """Get a Redis connection from the Celery broker."""
    settings = get_settings()
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def set_run_state(run_id: str, state: str, extra: dict | None = None) -> None:
    """Store run state in Redis or local cache with TTL."""
    data = {"state": state, "updated_at": datetime.now(UTC).isoformat()}
    if extra:
        data.update(extra)
    _local_state_cache[run_id] = data
    try:
        r = _get_redis()
        r.setex(f"{RUN_STATE_PREFIX}{run_id}", RUN_STATE_TTL, json.dumps(data))
    except Exception:
        pass


def get_run_state(run_id: str) -> dict | None:
    """Read run state from Redis or local cache."""
    try:
        r = _get_redis()
        raw = r.get(f"{RUN_STATE_PREFIX}{run_id}")
        if raw is not None:
            return json.loads(raw)
    except Exception:
        pass
    return _local_state_cache.get(run_id)


def get_run_states(run_ids: list[str]) -> dict[str, dict]:
    """Read many run states with one Redis round trip (status polls count every recent run)."""
    states: dict[str, dict] = {}
    if not run_ids:
        return states
    try:
        r = _get_redis()
        for run_id, raw in zip(run_ids, r.mget([f"{RUN_STATE_PREFIX}{rid}" for rid in run_ids])):
            if raw is not None:
                states[run_id] = json.loads(raw)
    except Exception:
        pass
    for run_id in run_ids:
        if run_id not in states and run_id in _local_state_cache:
            states[run_id] = _local_state_cache[run_id]
    return states


def mark_run_cancelled(run_id: str) -> None:
    """Durable cancel marker so workers skip release after cancel_run."""
    _local_cancelled_set.add(run_id)
    try:
        r = _get_redis()
        r.setex(f"{RUN_CANCELLED_PREFIX}{run_id}", RUN_STATE_TTL, "1")
    except Exception:
        pass


def is_run_cancelled(run_id: str) -> bool:
    try:
        if run_id in _local_cancelled_set:
            return True
        r = _get_redis()
        if bool(r.get(f"{RUN_CANCELLED_PREFIX}{run_id}")):
            return True
    except Exception:
        pass
    state = get_run_state(run_id) or {}
    return state.get("failure_category") == "cancelled"


def set_run_result(run_id: str, result: dict) -> None:
    """Store grading result in Redis or local cache with TTL."""
    _local_result_cache[run_id] = result
    try:
        r = _get_redis()
        r.setex(f"{RUN_RESULT_PREFIX}{run_id}", RUN_STATE_TTL, json.dumps(result))
    except Exception:
        pass


def get_run_result(run_id: str) -> dict | None:
    """Read grading result from Redis or local cache."""
    try:
        r = _get_redis()
        raw = r.get(f"{RUN_RESULT_PREFIX}{run_id}")
        if raw is not None:
            return json.loads(raw)
    except Exception:
        pass
    return _local_result_cache.get(run_id)


def _cancelled_response(run_id: str, message: str = "Sandbox run was cancelled before execution.") -> dict:
    return {
        "run_id": run_id,
        "success": False,
        "score": 0,
        "max_score": 0,
        "test_results": [],
        "warnings": [],
        "failure_category": "cancelled",
        "failure_message": message,
    }


def execute_sandbox_run(
    run_id: str,
    zip_data_b64: str,
    config: dict,
    artifact_refs: dict[str, str],
    allowed_concepts: list[str],
    stdin: str | None = None,
    expected_manifest: dict | None = None,
) -> dict:
    """Execute a sandbox grading run directly through the pipeline."""
    if is_run_cancelled(run_id):
        return _cancelled_response(run_id)

    set_run_state(run_id, "run")
    if is_run_cancelled(run_id):
        return _cancelled_response(run_id)

    started = time.monotonic()
    try:
        from app.domains.grading.engine import GradingEngine

        zip_data = base64.b64decode(zip_data_b64)
        config_obj = AssignmentConfigV1.model_validate(config)

        engine = GradingEngine(
            config=config_obj,
            artifact_refs=artifact_refs,
            allowed_concepts=allowed_concepts,
            expected_manifest=expected_manifest,
        )
        with audit_context(workflow_type="sandbox"):
            grading_result = engine.grade_submission_sync(zip_data=zip_data, stdin=stdin)

        if is_run_cancelled(run_id):
            return _cancelled_response(run_id, "Sandbox run was cancelled after pipeline execution.")

        result_dict = grading_result.to_dict(run_id=run_id)


        set_run_result(run_id, result_dict)
        record_grade_seconds(time.monotonic() - started)
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
                release_execution_slots(owner=run_id)
            except Exception as rel_err:
                logger.warning("Failed releasing sandbox slot for %s: %s", run_id, rel_err)

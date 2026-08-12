"""Judge0 pytest execution: runner packaging, submit/poll/delete, and parse.

Hides runner script writing, additional_files ZIP/base64 encoding, Judge0
lifecycle, status classification, and stdout parsing behind one entry point.
Scoring stays in the grading pipeline via :func:`calculate_scores`.
"""
from __future__ import annotations

import base64
import io
import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.domains.grading.result_parser import PytestRunResult, parse_pytest_json
from app.domains.grading.runner_gen import generate_runner_script
from app.integrations.judge0.client import (
    Judge0CleanupError,
    Judge0Error,
    create_judge0_client,
    judge0_failure_for_status,
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionOutcome:
    """Result of a Judge0 pytest execution (before rubric scoring)."""

    success: bool = False
    pytest_result: PytestRunResult | None = None
    failure_category: str | None = None
    failure_message: str | None = None


def _build_additional_files_b64(exec_dir: Path) -> str:
    """ZIP *exec_dir* for Judge0 ``additional_files`` (excludes ``runner.py`` if present)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in exec_dir.rglob("*"):
            if item.is_file() and item.name != "runner.py":
                zf.write(item, str(item.relative_to(exec_dir)))
    return base64.b64encode(buffer.getvalue()).decode("ascii")


async def execute_pytest_in_judge0(
    exec_dir: Path,
    *,
    test_filenames: list[str],
    test_cases: dict[str, dict[str, list[str]]],
    entrypoint_module: str,
    language_id: int,
    cpu_time_limit: float,
    dependencies: list[str] | None = None,
    memory_limit: int = 262144,
    stdin: str | None = None,
) -> ExecutionOutcome:
    """Generate runner, submit to Judge0, parse stdout, enforce cleanup.

    Args:
        stdin: Optional raw stdin text string passed to the Judge0 execution environment.

    Zero-retention: a Judge0 delete failure overrides any prior success and
    sets ``failure_category`` to ``cleanup_failure``.
    """
    outcome = ExecutionOutcome()
    runner_source = generate_runner_script(
        test_filenames,
        test_cases,
        entrypoint_module,
        dependencies,
    )
    # runner.py is Judge0 source_code only; exclude it from additional_files.
    additional_files_b64 = _build_additional_files_b64(exec_dir)

    token: str | None = None
    async with create_judge0_client() as judge0:
        try:
            token = await judge0.create_submission(
                source_code=runner_source,
                language_id=language_id,
                additional_files_b64=additional_files_b64,
                cpu_time_limit=cpu_time_limit,
                memory_limit=memory_limit,
                stdin=stdin if stdin else None,
            )
            submission_result = await judge0.poll_submission(token)

            status_id = submission_result.get("status", {}).get("id", 0)
            failure = judge0_failure_for_status(status_id)
            if failure is not None:
                outcome.failure_category, outcome.failure_message = failure
                return outcome

            stdout = submission_result.get("stdout", "") or ""
            pytest_result = parse_pytest_json(stdout)
            outcome.pytest_result = pytest_result

            if pytest_result.error_message:
                outcome.failure_category = "test_failure"
                outcome.failure_message = pytest_result.error_message
                return outcome

            outcome.success = True
            return outcome

        except Judge0Error as exc:
            outcome.failure_category = "judge0_error"
            outcome.failure_message = str(exc)
            return outcome

        finally:
            if token is not None:
                try:
                    await judge0.delete_submission(token)
                except Judge0CleanupError:
                    logger.error(
                        "CLEANUP FAILURE: Could not delete Judge0 submission %s. "
                        "This is a launch-blocking violation of the zero-retention contract.",
                        token,
                    )
                    outcome.failure_category = "cleanup_failure"
                    outcome.failure_message = (
                        "Judge0 submission cleanup failed. "
                        "This is a zero-retention violation."
                    )
                    outcome.success = False

    return outcome

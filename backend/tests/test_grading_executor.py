"""Tests for the concrete Judge0 pytest executor."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.domains.grading.executor import (
    ExecutionOutcome,
    execute_pytest_in_judge0,
)
from app.integrations.judge0.client import Judge0CleanupError, Judge0Error


def _mock_judge0_client(
    *,
    submission_result: dict | None = None,
    create_error: Exception | None = None,
    delete_error: Exception | None = None,
) -> MagicMock:
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    if create_error is not None:
        client.create_submission = AsyncMock(side_effect=create_error)
    else:
        client.create_submission = AsyncMock(return_value="tok-1")

    client.poll_submission = AsyncMock(
        return_value=submission_result
        or {
            "status": {"id": 3},
            "stdout": '---AUTOGRADER_RESULTS---\n{"tests": [], "summary": {"total": 0, "passed": 0, "failed": 0, "errors": 0, "duration": 0.0, "exit_code": 0}}',
        }
    )

    if delete_error is not None:
        client.delete_submission = AsyncMock(side_effect=delete_error)
    else:
        client.delete_submission = AsyncMock(return_value=True)

    return client


@pytest.mark.asyncio
async def test_executor_success_parses_stdout(tmp_path):
    client = _mock_judge0_client()
    with patch(
        "app.domains.grading.executor.create_judge0_client", return_value=client
    ):
        outcome = await execute_pytest_in_judge0(
            tmp_path,
            test_filenames=["tests.py"],
            test_cases={},
            entrypoint_module="main",
            language_id=71,
            cpu_time_limit=10.0,
        )

    assert outcome.success is True
    assert outcome.pytest_result is not None
    assert outcome.pytest_result.exit_code == 0
    assert not (tmp_path / "runner.py").exists()
    client.create_submission.assert_awaited_once()
    assert "def pytest_generate_tests" in client.create_submission.await_args.kwargs["source_code"]
    client.delete_submission.assert_awaited_once_with("tok-1")


@pytest.mark.asyncio
async def test_executor_uses_status_map_for_timeout(tmp_path):
    client = _mock_judge0_client(
        submission_result={"status": {"id": 5}, "stdout": ""}
    )
    with patch(
        "app.domains.grading.executor.create_judge0_client", return_value=client
    ):
        outcome = await execute_pytest_in_judge0(
            tmp_path,
            test_filenames=["tests.py"],
            test_cases={},
            entrypoint_module="main",
            language_id=71,
            cpu_time_limit=10.0,
        )

    assert outcome.success is False
    assert outcome.failure_category == "timeout"
    assert "timed out" in (outcome.failure_message or "").lower()


@pytest.mark.asyncio
async def test_executor_runtime_error_is_timeout_per_map(tmp_path):
    """Statuses 7–12 map to timeout (map is source of truth)."""
    client = _mock_judge0_client(
        submission_result={"status": {"id": 11}, "stdout": ""}
    )
    with patch(
        "app.domains.grading.executor.create_judge0_client", return_value=client
    ):
        outcome = await execute_pytest_in_judge0(
            tmp_path,
            test_filenames=["tests.py"],
            test_cases={},
            entrypoint_module="main",
            language_id=71,
            cpu_time_limit=10.0,
        )

    assert outcome.failure_category == "timeout"


@pytest.mark.asyncio
async def test_executor_parse_failure(tmp_path):
    client = _mock_judge0_client(
        submission_result={"status": {"id": 3}, "stdout": "no json here"}
    )
    with patch(
        "app.domains.grading.executor.create_judge0_client", return_value=client
    ):
        outcome = await execute_pytest_in_judge0(
            tmp_path,
            test_filenames=["tests.py"],
            test_cases={},
            entrypoint_module="main",
            language_id=71,
            cpu_time_limit=10.0,
        )

    assert outcome.success is False
    assert outcome.failure_category == "test_failure"
    assert outcome.pytest_result is not None
    assert outcome.pytest_result.error_message


@pytest.mark.asyncio
async def test_executor_cleanup_failure_overrides_success(tmp_path):
    client = _mock_judge0_client(
        delete_error=Judge0CleanupError("delete failed")
    )
    with patch(
        "app.domains.grading.executor.create_judge0_client", return_value=client
    ):
        outcome = await execute_pytest_in_judge0(
            tmp_path,
            test_filenames=["tests.py"],
            test_cases={},
            entrypoint_module="main",
            language_id=71,
            cpu_time_limit=10.0,
        )

    assert outcome.success is False
    assert outcome.failure_category == "cleanup_failure"


@pytest.mark.asyncio
async def test_executor_judge0_error(tmp_path):
    client = _mock_judge0_client(create_error=Judge0Error("boom"))
    with patch(
        "app.domains.grading.executor.create_judge0_client", return_value=client
    ):
        outcome = await execute_pytest_in_judge0(
            tmp_path,
            test_filenames=["tests.py"],
            test_cases={},
            entrypoint_module="main",
            language_id=71,
            cpu_time_limit=10.0,
        )

    assert outcome == ExecutionOutcome(
        success=False,
        failure_category="judge0_error",
        failure_message="boom",
    )

"""Unit tests for the deep GradingEngine domain module."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.engine import GradingEngine, GradingResult
from app.domains.grading.executor import ExecutionOutcome
from app.domains.grading.result_parser import PytestRunResult, PytestTestResult


def create_zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)
    return buffer.getvalue()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def base_config() -> AssignmentConfigV1:
    config_dict = {
        "bundle": {
            "entrypoint": "main.py",
            "file_requirements": [
                {"label": "Main file", "paths": ["main.py"]},
            ],
        },
        "artifacts": {
            "assignment_tests": {
                "type": "pytest_file",
                "display_filename": "tests.py",
            }
        },
        "scoring_items": [
            {
                "key": "test_pass",
                "label": "Test Pass",
                "points": 10,
                "extra_credit": False,
                "item_type": "pytest",
            }
        ],
    }
    return AssignmentConfigV1.model_validate(config_dict)


@pytest.mark.anyio
async def test_grading_engine_unsafe_zip(base_config: AssignmentConfigV1) -> None:
    engine = GradingEngine(config=base_config, artifact_refs={}, allowed_concepts=["functions"])
    bad_zip = b"NOT_A_ZIP_FILE"

    result = await engine.grade_submission(bad_zip)
    assert not result.success
    assert result.failure_category == "unsafe_zip"


@pytest.mark.anyio
async def test_grading_engine_missing_required_file(base_config: AssignmentConfigV1) -> None:
    engine = GradingEngine(config=base_config, artifact_refs={}, allowed_concepts=["functions"])
    zip_bytes = create_zip_bytes({"other.py": b"print('hello')"})

    result = await engine.grade_submission(zip_bytes)
    assert not result.success
    assert result.failure_category == "missing_required_file"


@pytest.mark.anyio
async def test_grading_engine_concept_blocked(base_config: AssignmentConfigV1) -> None:
    engine = GradingEngine(config=base_config, artifact_refs={}, allowed_concepts=["functions"])
    zip_bytes = create_zip_bytes({"main.py": b"import subprocess\nsubprocess.run('ls')"})

    result = await engine.grade_submission(zip_bytes)
    assert not result.success
    assert result.failure_category == "concept_blocked"
    assert "subprocess" in result.failure_message


@pytest.mark.anyio
async def test_grading_engine_success(base_config: AssignmentConfigV1, tmp_path: Path) -> None:
    tests_file = tmp_path / "tests.py"
    tests_file.write_text("def test_pass(): pass", encoding="utf-8")
    artifact_refs = {"assignment_tests": f"file://{tests_file.as_posix()}"}

    engine = GradingEngine(config=base_config, artifact_refs=artifact_refs, allowed_concepts=["functions"])
    zip_bytes = create_zip_bytes({"main.py": b"def main(): pass"})

    simulated_pytest = PytestRunResult(
        tests=[
            PytestTestResult(nodeid="test_pass", outcome="passed", markers=["ag_test_pass"], duration=0.01, message=None)
        ],
        total=1,
        passed=1,
        failed=0,
        errors=0,
        duration=0.05,
        exit_code=0,
    )
    mock_outcome = ExecutionOutcome(success=True, pytest_result=simulated_pytest)

    with patch("app.domains.grading.engine.execute_pytest_in_judge0", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_outcome
        result = await engine.grade_submission(zip_bytes)

    assert result.success
    assert result.score == 10
    assert result.max_score == 10
    assert result.pytest_result.passed == 1

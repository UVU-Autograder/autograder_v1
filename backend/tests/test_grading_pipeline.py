"""Unit tests for the unified GradingPipeline service."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.executor import ExecutionOutcome
from app.domains.grading.pipeline import (
    GradingPipeline,
    SubmissionPayload,
)
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


def test_submission_payload_validation() -> None:
    # 0 sources
    empty = SubmissionPayload()
    with pytest.raises(ValueError, match="Provide exactly one"):
        empty.validate()

    # 2 sources
    double = SubmissionPayload(zip_data=b"abc", files={"a.py": b"123"})
    with pytest.raises(ValueError, match="Provide exactly one"):
        double.validate()

    # 1 source valid
    single = SubmissionPayload.from_files({"main.py": b"pass"})
    single.validate()


@pytest.mark.anyio
async def test_pipeline_unsafe_zip(base_config: AssignmentConfigV1) -> None:
    pipeline = GradingPipeline(config=base_config, artifact_refs={}, allowed_concepts=["functions"])
    payload = SubmissionPayload.from_zip(b"NOT_A_VALID_ZIP")

    report = await pipeline.evaluate(payload)
    assert not report.success
    assert report.failure_category == "unsafe_zip"


@pytest.mark.anyio
async def test_pipeline_unsafe_file_traversal(base_config: AssignmentConfigV1) -> None:
    pipeline = GradingPipeline(config=base_config, artifact_refs={}, allowed_concepts=["functions"])
    payload = SubmissionPayload.from_files({"../../evil.py": b"evil"})

    report = await pipeline.evaluate(payload)
    assert not report.success
    assert report.failure_category == "unsafe_path"
    assert "Path traversal attempt" in (report.failure_message or "")


@pytest.mark.anyio
async def test_pipeline_missing_required_file(base_config: AssignmentConfigV1) -> None:
    pipeline = GradingPipeline(config=base_config, artifact_refs={}, allowed_concepts=["functions"])
    payload = SubmissionPayload.from_files({"other.py": b"print('hello')"})

    report = await pipeline.evaluate(payload)
    assert not report.success
    assert report.failure_category == "missing_required_file"


@pytest.mark.anyio
async def test_pipeline_concept_blocked(base_config: AssignmentConfigV1) -> None:
    pipeline = GradingPipeline(config=base_config, artifact_refs={}, allowed_concepts=["functions"])
    payload = SubmissionPayload.from_files({"main.py": b"import subprocess\nsubprocess.run('ls')"})

    report = await pipeline.evaluate(payload)
    assert not report.success
    assert report.failure_category == "concept_blocked"
    assert "subprocess" in (report.failure_message or "")


@pytest.mark.anyio
async def test_pipeline_evaluate_success_and_sync(base_config: AssignmentConfigV1, tmp_path: Path) -> None:
    tests_file = tmp_path / "tests.py"
    tests_file.write_text("def test_pass(): pass", encoding="utf-8")
    artifact_refs = {"assignment_tests": f"file://{tests_file.as_posix()}"}

    mock_outcome = ExecutionOutcome(
        success=True,
        pytest_result=PytestRunResult(
            tests=[
                PytestTestResult(
                    nodeid="test_pass",
                    outcome="passed",
                    markers=["ag_test_pass"],
                    duration=0.01,
                    message=None,
                )
            ],
            total=1,
            passed=1,
            failed=0,
            errors=0,
            duration=0.05,
            exit_code=0,
        ),
    )

    mock_executor = AsyncMock(return_value=mock_outcome)
    pipeline = GradingPipeline(
        config=base_config,
        artifact_refs=artifact_refs,
        allowed_concepts=["functions"],
        executor_fn=mock_executor,
    )

    payload = SubmissionPayload.from_files({"main.py": b"def main(): pass"})
    report = await pipeline.evaluate(payload)

    assert report.success
    assert report.score == 10
    assert report.max_score == 10
    assert len(report.test_results) == 1
    assert report.pytest_result is not None
    assert report.pytest_result.passed == 1

    # Verify sync execution
    sync_report = pipeline.evaluate_sync(payload)
    assert sync_report.success
    assert sync_report.score == 10

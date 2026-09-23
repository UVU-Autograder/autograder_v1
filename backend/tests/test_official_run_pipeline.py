import csv
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.domains.grading.engine import GradingResult
from app.domains.runs.mock_runner import run_mock_official_run
from app.domains.runs.models import RunSummary
from app.domains.runs.tasks import (
    build_model_solution_zip,
    failing_automated_items,
    grade_official_run,
)
from test_ingestion_extractor import create_zip_bytes
from dispatch_helpers import drain


def test_build_model_solution_zip_uses_real_files():
    payload = build_model_solution_zip(
        ["dessert.py", "dessertshop.py"],
        {
            "dessert.py": b"class Dessert: pass\n",
            "dessertshop.py": b"print('ok')\n",
        },
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert archive.namelist() == ["dessert.py", "dessertshop.py"]
        assert archive.read("dessertshop.py") == b"print('ok')\n"


def test_build_model_solution_zip_rejects_missing_required_file():
    with pytest.raises(ValueError, match="dessertshop.py"):
        build_model_solution_zip(
            ["dessert.py", "dessertshop.py"],
            {"dessert.py": b"class Dessert: pass\n"},
        )


def test_model_validation_accepts_only_explicitly_passed_items():
    passed = {"key": "behavior", "passed": True}
    failed = {"key": "style", "passed": False}

    assert failing_automated_items([passed]) == []
    assert failing_automated_items([passed, failed]) == [failed]


def test_failing_automated_items_ignores_manual_rubric_items():
    """Manual items never pass (no pytest runs), so they must not fail validation.

    Regression: model-solution validation failed ds5, ds6, lab1, lab3, lab4, lab6
    and lab7 on their manual items ("Test case 'reflection' failed: None").
    """
    manual = {"key": "reflection", "item_type": "manual", "passed": False}
    auto_fail = {"key": "sorting", "item_type": "pytest", "passed": False}
    auto_pass = {"key": "init", "item_type": "pytest", "passed": True}
    assert failing_automated_items([manual, auto_pass]) == []
    assert failing_automated_items([manual, auto_fail]) == [auto_fail]


@pytest.fixture(autouse=True)
def db_session(reset_database):
    with SessionLocal() as session:
        yield session


@pytest.fixture()
def temp_workspaces(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from app.core.settings import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    return tmp_path


def test_run_mock_official_run_success(db_session: Session, temp_workspaces: Path) -> None:
    # 1. Create a RunSummary record
    run = RunSummary(
        workflow_type="official",
        assignment_id=1,  # seeded assignment
        status="queue",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    # 2. Run mock official run
    run_mock_official_run(run.id)

    # 3. Verify database updates
    db_session.refresh(run)
    assert run.status == "complete"
    assert run.success_count == 1
    assert run.warning_count == 1
    assert run.failure_count == 1

    # 4. Verify generated workspace files
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    run_dir = workspaces_dir / f"official_{run.id}"

    assert (run_dir / "run_details.json").exists()
    assert (run_dir / "grades.csv").exists()
    assert (run_dir / "feedback.zip").exists()

    # Check grades CSV contents
    with open(run_dir / "grades.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows[0] == ["Student Identifier", "Canvas User ID", "Submission ID", "Score", "Max Score"]
        assert len(rows) == 4  # Header + 3 students


def test_grade_official_run_pipeline_success(db_session: Session, temp_workspaces: Path) -> None:
    # 1. Create a RunSummary record
    run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        status="queue",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    # 2. Save a Canvas export ZIP file in the workspaces folder
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    workspaces_dir.mkdir(parents=True, exist_ok=True)
    zip_dest = workspaces_dir / f"official_{run.id}.zip"

    # ZIP contains student files matching canvas pattern
    canvas_zip_bytes = create_zip_bytes({
        "studenta_11111_67890_student_functions.py": b"print('hello')",
        "studentb_22222_67891_student_functions.py": b"print('hello')"
    })
    zip_dest.write_bytes(canvas_zip_bytes)

    # 3. Mock GradingEngine.grade_submission
    mock_result = GradingResult(
        success=True,
        score=100,
        max_score=100,
        test_results=[{"key": "test_add", "label": "test_add", "points": 100, "points_awarded": 100, "passed": True}],
        warnings=[]
    )

    with patch("app.domains.grading.engine.GradingEngine.grade_submission", new_callable=AsyncMock) as mock_pipeline:
        mock_pipeline.return_value = mock_result

        # Run task directly
        result = drain(run.id)

        assert mock_pipeline.call_count == 2  # 2 students in zip
        assert all(
            call.kwargs.get("bundle_dir") is not None or (
                len(call.args) == 0 and "bundle_dir" in call.kwargs
            )
            for call in mock_pipeline.call_args_list
        )
        for call in mock_pipeline.call_args_list:
            assert call.kwargs.get("zip_data") is None
            assert call.kwargs.get("bundle_dir") is not None
        assert result["state"] == "complete"
        assert "student_results" not in result
        assert grade_official_run.ignore_result is True

    # 4. Verify DB and files
    db_session.refresh(run)
    assert run.status == "complete"
    assert run.success_count == 2
    assert run.failure_count == 0

    run_dir = workspaces_dir / f"official_{run.id}"
    assert (run_dir / "run_details.json").exists()
    assert (run_dir / "grades.csv").exists()
    assert (run_dir / "feedback.zip").exists()
    details = json.loads((run_dir / "run_details.json").read_text(encoding="utf-8"))
    assert details["run_status"] == "complete"
    assert len(details["student_results"]) == 2


def test_grade_official_run_writes_incremental_details(
    db_session: Session,
    temp_workspaces: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "judge0_max_concurrent", 1)

    run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        status="queue",
        total_submission_count=2,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    workspaces_dir.mkdir(parents=True, exist_ok=True)
    zip_dest = workspaces_dir / f"official_{run.id}.zip"
    zip_dest.write_bytes(
        create_zip_bytes({
            "studenta_11111_67890_student_functions.py": b"print('hello')",
            "studentb_22222_67891_student_functions.py": b"print('hello')",
        })
    )

    mock_result = GradingResult(success=True, score=100, max_score=100, test_results=[], warnings=[])
    seen_counts: list[int] = []
    run_dir = workspaces_dir / f"official_{run.id}"

    async def grade_and_observe(*args, **kwargs):
        details_file = run_dir / "run_details.json"
        assert details_file.exists()
        payload = json.loads(details_file.read_text(encoding="utf-8"))
        seen_counts.append(len(payload.get("student_results", {})))
        return mock_result

    with patch(
        "app.domains.grading.engine.GradingEngine.grade_submission",
        new_callable=AsyncMock,
        side_effect=grade_and_observe,
    ):
        drain(run.id)

    assert seen_counts[0] == 0
    assert 1 in seen_counts
    final = json.loads((run_dir / "run_details.json").read_text(encoding="utf-8"))
    assert len(final["student_results"]) == 2
    assert final["run_status"] == "complete"


def test_cleanup_expired_workspaces(db_session: Session, temp_workspaces: Path) -> None:
    from datetime import UTC, datetime, timedelta

    from app.domains.runs.tasks import cleanup_expired_workspaces

    # 1. Create a run that is 25 hours old (expired)
    expired_time = datetime.now(UTC) - timedelta(hours=25)
    expired_run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        status="complete",
        created_at=expired_time,
    )
    db_session.add(expired_run)

    # 2. Create a run that is 5 hours old (not expired)
    recent_time = datetime.now(UTC) - timedelta(hours=5)
    recent_run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        status="complete",
        created_at=recent_time,
    )
    db_session.add(recent_run)
    db_session.commit()
    db_session.refresh(expired_run)
    db_session.refresh(recent_run)

    # 3. Create workspace directory and ZIP file for both
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    workspaces_dir.mkdir(parents=True, exist_ok=True)

    expired_run_dir = workspaces_dir / f"official_{expired_run.id}"
    expired_run_dir.mkdir(parents=True, exist_ok=True)
    (expired_run_dir / "run_details.json").write_text("{}")
    expired_zip = workspaces_dir / f"official_{expired_run.id}.zip"
    expired_zip.write_text("dummy zip content")

    recent_run_dir = workspaces_dir / f"official_{recent_run.id}"
    recent_run_dir.mkdir(parents=True, exist_ok=True)
    (recent_run_dir / "run_details.json").write_text("{}")
    recent_zip = workspaces_dir / f"official_{recent_run.id}.zip"
    recent_zip.write_text("dummy zip content")

    # 4. Run the cleanup task
    result = cleanup_expired_workspaces()
    assert result["cleaned_runs_count"] == 1
    assert result["error_count"] == 0

    # 5. Verify expired files are deleted
    assert not expired_run_dir.exists()
    assert not expired_zip.exists()

    # 6. Verify recent files are NOT deleted
    assert recent_run_dir.exists()
    assert recent_zip.exists()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_run_grading_pipeline_multi_file_ast_block(db_session: Any, temp_workspaces: Any) -> None:
    from app.domains.assignments.schemas import AssignmentConfigV1
    from app.domains.grading.engine import GradingEngine

    # Create configuration for an assignment
    config_dict = {
        "bundle": {
            "entrypoint": "main.py",
            "file_requirements": [
                {"label": "Main file", "paths": ["main.py"]},
                {"label": "Helper file", "paths": ["helper.py"]}
            ]
        },
        "artifacts": {
            "assignment_tests": {
                "type": "pytest_file",
                "display_filename": "tests.py"
            }
        },
        "scoring_items": [
            {
                "key": "t1",
                "label": "Test 1",
                "points": 10,
                "extra_credit": False,
                "item_type": "pytest",
            }
        ]
    }
    config = AssignmentConfigV1.model_validate(config_dict)

    # ZIP contains student files: helper.py contains unsafe import (subprocess)
    # but main.py is clean.
    zip_bytes = create_zip_bytes({
        "main.py": b"print('clean main')",
        "helper.py": b"import subprocess\nsubprocess.run('echo hello')"
    })

    # Create test artifact file on disk
    tests_file = temp_workspaces / "tests.py"
    tests_file.write_text("def test_ok(): pass", encoding="utf-8")

    artifact_refs = {
        "assignment_tests": f"file://{tests_file.as_posix()}"
    }

    engine = GradingEngine(
        config=config,
        artifact_refs=artifact_refs,
        allowed_concepts=["variables", "functions"]
    )
    result = await engine.grade_submission(zip_data=zip_bytes)

    # Check that it got blocked by helper.py, not main.py!
    assert not result.success
    assert result.failure_category == "concept_blocked"
    assert "[helper.py]" in result.failure_message
    assert "subprocess" in result.failure_message


@pytest.mark.anyio
async def test_run_grading_pipeline_ds1_success(db_session: Session, temp_workspaces: Path) -> None:
    from app.domains.assignments.schemas import AssignmentConfigV1
    from app.domains.assignments.service import get_assignment_for_course
    from app.domains.grading.engine import GradingEngine
    from app.domains.grading.executor import ExecutionOutcome
    from app.domains.grading.result_parser import PytestRunResult, PytestTestResult

    # 1. Retrieve the seeded ds1 assignment
    assignment = get_assignment_for_course(db_session, "cs1410", "ds1")
    assert assignment is not None
    assert assignment.config is not None

    # Load configuration
    config = AssignmentConfigV1.model_validate(assignment.config.config_json)

    # 2. Get artifact refs
    artifact_refs = {}
    for artifact in assignment.artifacts:
        artifact_refs[artifact.artifact_key] = artifact.storage_ref

    # 3. Create student submission ZIP with dessert.py solution
    repo_root = Path(__file__).resolve().parents[2]
    model_solution_path = repo_root / "backend" / "app" / "db" / "seeds" / "ds1" / "dessert.py"
    dessert_content = model_solution_path.read_bytes()

    zip_bytes = create_zip_bytes({
        "dessert.py": dessert_content
    })

    # 4. Mock the Judge0 execution to return 5 passed tests
    simulated_result = PytestRunResult(
        tests=[
            PytestTestResult(nodeid="test_dessert_item_class", outcome="passed", markers=["ag_dessert_item"], duration=0.01, message=None),
            PytestTestResult(nodeid="test_candy_class", outcome="passed", markers=["ag_candy"], duration=0.01, message=None),
            PytestTestResult(nodeid="test_cookie_class", outcome="passed", markers=["ag_cookie"], duration=0.01, message=None),
            PytestTestResult(nodeid="test_icecream_class", outcome="passed", markers=["ag_icecream"], duration=0.01, message=None),
            PytestTestResult(nodeid="test_sundae_class", outcome="passed", markers=["ag_sundae"], duration=0.01, message=None),
        ],
        total=5,
        passed=5,
        failed=0,
        errors=0,
        duration=0.1,
        exit_code=0,
    )
    mock_outcome = ExecutionOutcome(success=True, pytest_result=simulated_result)

    from app.domains.assignments.service import effective_allowed_concepts
    allowed = effective_allowed_concepts(assignment)

    with patch("app.domains.grading.engine.execute_pytest_in_judge0", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = mock_outcome

        engine = GradingEngine(
            config=config,
            artifact_refs=artifact_refs,
            allowed_concepts=allowed,
        )
        result = await engine.grade_submission(zip_data=zip_bytes)

    # 5. Assert it graded perfectly!
    assert result.success
    assert result.score == 100
    assert result.max_score == 100
    assert len(result.warnings) == 0
    assert result.pytest_result is not None
    assert result.pytest_result.total == 5
    assert result.pytest_result.passed == 5
    assert result.pytest_result.failed == 0




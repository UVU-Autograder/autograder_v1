import sys
import os
import zipfile
import json
import csv
from pathlib import Path
from unittest.mock import patch, AsyncMock
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base, import_domain_models
from app.db.seed import initialize_database
from app.db.session import SessionLocal, engine
from app.domains.runs.models import RunSummary
from app.domains.runs.tasks import grade_official_run, run_mock_official_run
from app.domains.grading.service import GradingResult
from app.core.settings import get_settings
from test_ingestion_extractor import create_zip_bytes


@pytest.fixture(autouse=True)
def db_session():
    import_domain_models()
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)


@pytest.fixture()
def temp_workspaces(tmp_path, monkeypatch):
    from app.core.settings import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    return tmp_path


def test_run_mock_official_run_success(db_session, temp_workspaces):
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


def test_grade_official_run_pipeline_success(db_session, temp_workspaces):
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

    # 3. Mock run_grading_pipeline
    mock_result = GradingResult(
        success=True,
        score=100,
        max_score=100,
        test_results=[{"key": "test_add", "label": "test_add", "points": 100, "points_awarded": 100, "passed": True}],
        warnings=[]
    )

    with patch("app.domains.grading.service.run_grading_pipeline", new_callable=AsyncMock) as mock_pipeline:
        mock_pipeline.return_value = mock_result

        # Run task directly
        result = grade_official_run(run.id)

        assert mock_pipeline.call_count == 2  # 2 students in zip
        assert "student_results" in result

    # 4. Verify DB and files
    db_session.refresh(run)
    assert run.status == "complete"
    assert run.success_count == 2
    assert run.failure_count == 0

    run_dir = workspaces_dir / f"official_{run.id}"
    assert (run_dir / "run_details.json").exists()
    assert (run_dir / "grades.csv").exists()
    assert (run_dir / "feedback.zip").exists()


def test_cleanup_expired_workspaces(db_session, temp_workspaces):
    from datetime import datetime, timedelta, UTC
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
    assert len(result["errors"]) == 0

    # 5. Verify expired files are deleted
    assert not expired_run_dir.exists()
    assert not expired_zip.exists()

    # 6. Verify recent files are NOT deleted
    assert recent_run_dir.exists()
    assert recent_zip.exists()


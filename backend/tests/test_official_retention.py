from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.auth_utils import create_access_token
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.domains.runs import retention
from app.domains.runs.cleanup_worker import sweep
from app.domains.runs.models import RunSummary
from app.domains.runs.router import _retained_download
from app.domains.runs.tasks import grade_official_run
from app.main import create_app


@pytest.fixture
def workspace(tmp_path, monkeypatch, reset_database):
    monkeypatch.setattr(get_settings(), "artifact_storage_dir", str(tmp_path / "artifacts"))
    return tmp_path


@pytest.fixture
def run(workspace):
    with SessionLocal() as db:
        value = RunSummary(workflow_type="official", assignment_id=1, status="complete",
                           total_submission_count=1)
        db.add(value)
        db.commit()
        db.refresh(value)
        root = retention.workspace_root()
        directory = root / f"official_{value.id}"
        directory.mkdir(parents=True)
        (directory / "run_details.json").write_text('{"student_results": {}}')
        (root / f"official_{value.id}.zip").write_bytes(b"private-code")
        yield value


def endpoint(run: RunSummary) -> str:
    return f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}"


def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(email='dev.staff@uvu.edu')}"}


def expire(run: RunSummary, monkeypatch) -> None:
    monkeypatch.setattr(retention, "utc_now", lambda: retention.review_expiry(run))


def test_deadline_boundary_and_unchanged_intake(run, monkeypatch):
    assert retention.deletion_deadline(run) - retention.review_expiry(run) == timedelta(hours=1)
    monkeypatch.setattr(retention, "utc_now", lambda: retention.review_expiry(run) - timedelta(microseconds=1))
    with retention.access(run.id):
        pass
    expire(run, monkeypatch)
    with pytest.raises(HTTPException) as error:
        with retention.access(run.id):
            pytest.fail("Expired run was accessible")
    assert error.value.status_code == 410
    assert sweep()
    assert not (retention.workspace_root() / f"official_{run.id}").exists()
    assert not (retention.workspace_root() / f"official_{run.id}.zip").exists()


def test_partial_deletion_is_tombstoned_and_retried(run, monkeypatch, caplog):
    original = retention.shutil.rmtree
    def fail(*args, **kwargs):
        raise PermissionError("secret-student-name/private-code")
    monkeypatch.setattr(retention.shutil, "rmtree", fail)
    with SessionLocal() as db:
        assert not retention.cleanup(run.id, db, manual=True)
        saved = retention.load_run(db, run.id)
        assert saved.retention_state == "cleanup_failed"
        assert saved.cleanup_failure_category == "workspace_deletion_failed"
        assert not (retention.workspace_root() / f"official_{run.id}.zip").exists()
    with pytest.raises(HTTPException) as error:
        with retention.access(run.id):
            pass
    assert error.value.status_code == 410
    assert "secret-student-name" not in caplog.text
    monkeypatch.setattr(retention.shutil, "rmtree", original)
    assert sweep()
    with SessionLocal() as db:
        assert retention.load_run(db, run.id).retention_state == "deleted"
        assert retention.cleanup(run.id, db, manual=True)


def test_false_success_is_detected(run, monkeypatch):
    monkeypatch.setattr(retention.shutil, "rmtree", lambda *args: None)
    with SessionLocal() as db:
        assert not retention.cleanup(run.id, db, manual=True)
        assert retention.load_run(db, run.id).retention_state == "cleanup_failed"


@pytest.mark.parametrize("state", ["queue", "run"])
def test_manual_cleanup_rejects_active_run(run, state):
    with SessionLocal() as db:
        value = db.get(RunSummary, run.id)
        value.status = state
        db.commit()
    response = TestClient(create_app()).post(endpoint(run) + "/cleanup", headers=auth())
    assert response.status_code == 409
    assert (retention.workspace_root() / f"official_{run.id}.zip").exists()


@pytest.mark.parametrize("suffix,method", [
    ("/details", "get"), ("/export/csv", "get"), ("/export/feedback", "get"),
    ("/students/123/files", "get"), ("/students/123/files/content?filepath=x.py", "get"),
    ("/students/123/manual-grades", "post"),
])
def test_expired_endpoints_authorize_first(run, monkeypatch, suffix, method):
    expire(run, monkeypatch)
    client = TestClient(create_app())
    kwargs = {"json": {"grades": {}}} if method == "post" else {}
    request = getattr(client, method)
    assert request(endpoint(run) + suffix, **kwargs).status_code == 401
    response = request(endpoint(run) + suffix, headers=auth(), **kwargs)
    assert response.status_code == 410
    assert response.headers["cache-control"] == "no-store"
    assert client.get(endpoint(run), headers=auth()).status_code == 200


def test_cleanup_failure_api_is_sanitized(run, monkeypatch):
    def fail(*args):
        raise PermissionError("private identifier")
    monkeypatch.setattr(retention, "_delete_files", fail)
    response = TestClient(create_app()).post(endpoint(run) + "/cleanup", headers=auth())
    assert response.status_code == 503
    assert "private identifier" not in response.text
    response = TestClient(create_app()).get(endpoint(run), headers=auth())
    assert response.json()["retention_state"] == "cleanup_failed"


def test_stream_rechecks_expiry_without_holding_file_open(run, monkeypatch):
    path = retention.workspace_root() / f"official_{run.id}" / "grades.csv"
    path.write_bytes(b"x" * 150000)
    response = _retained_download(run.id, path=path, filename="grades.csv", media_type="text/csv")

    async def consume():
        iterator = response.body_iterator
        first = await anext(iterator)
        assert len(first) == 65536
        expire(run, monkeypatch)
        assert sweep()  # Windows deletion proves no open file survives a chunk.
        with pytest.raises(HTTPException):
            await anext(iterator)
    asyncio.run(consume())


def test_database_outage_fails_closed_and_does_not_delete(run, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OperationalError("", {}, Exception("private-code"))
    monkeypatch.setattr(retention, "load_run", unavailable)
    with pytest.raises(HTTPException) as error:
        with retention.access(run.id):
            pass
    assert error.value.status_code == 503
    assert not sweep()
    assert (retention.workspace_root() / f"official_{run.id}.zip").exists()
    assert "private-code" not in (retention.control_root() / "heartbeat.json").read_text()


def test_reconciliation_independent_of_redis_and_restart(run, monkeypatch):
    expire(run, monkeypatch)
    with patch("redis.Redis.from_url", side_effect=RuntimeError("redis offline")):
        assert sweep()
        assert sweep()
    with SessionLocal() as db:
        assert retention.health(db)["cleanup_service_healthy"]


def test_orphan_scan_preserves_unknown_and_instructor_paths(workspace):
    root = retention.workspace_root()
    root.mkdir()
    (root / "official_900").mkdir()
    (root / "official_900.zip").write_bytes(b"old")
    (root / "sandbox_900").mkdir()
    (root / "official_invalid.zip").write_bytes(b"unknown")
    with SessionLocal() as db:
        result = retention.reconcile(db)
    assert result["orphaned_cleaned_count"] == 1
    assert (root / "sandbox_900").exists()
    assert (root / "official_invalid.zip").exists()


def test_symlink_target_is_never_removed(run, workspace, monkeypatch):
    outside = workspace / "instructor.py"
    outside.write_text("must survive")
    link = retention.workspace_root() / f"official_{run.id}" / "linked.py"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Host does not permit symlink creation")
    expire(run, monkeypatch)
    assert not sweep()
    assert outside.read_text() == "must survive"
    with SessionLocal() as db:
        assert retention.load_run(db, run.id).retention_state == "cleanup_failed"


def test_cross_process_lock_busy_and_released_on_termination(run, workspace, monkeypatch):
    script = """
import sys, time
from app.core.settings import get_settings
from app.domains.runs.retention import run_lock
get_settings().artifact_storage_dir = sys.argv[1]
with run_lock(int(sys.argv[2])):
    print('locked', flush=True)
    time.sleep(30)
"""
    child = subprocess.Popen([sys.executable, "-c", script, str(workspace / "artifacts"), str(run.id)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == "locked"
        expire(run, monkeypatch)
        with SessionLocal() as db:
            assert retention.reconcile(db)["busy_count"] == 1
        assert (retention.workspace_root() / f"official_{run.id}").exists()
    finally:
        child.terminate()
        child.communicate(timeout=10)
    assert sweep()
    assert not (retention.workspace_root() / f"official_{run.id}").exists()


def test_expired_task_and_duplicate_delivery_never_recreate_files(run, monkeypatch):
    with SessionLocal() as db:
        value = db.get(RunSummary, run.id)
        value.status = "queue"
        db.commit()
    expire(run, monkeypatch)
    assert sweep()
    with patch("app.domains.runs.tasks.release_execution_slots") as release:
        grade_official_run(run.id)
        grade_official_run(run.id)
        release.assert_not_called()  # Tokenless legacy deliveries cannot own capacity.
    assert not (retention.workspace_root() / f"official_{run.id}").exists()


def test_expiry_during_execution_discards_result_and_releases_slots(run, monkeypatch):
    from app.domains.grading.engine import GradingResult
    from test_ingestion_extractor import create_zip_bytes

    with SessionLocal() as db:
        value = db.get(RunSummary, run.id)
        value.status = "queue"
        db.commit()
    archive = retention.workspace_root() / f"official_{run.id}.zip"
    archive.write_bytes(create_zip_bytes({"student_123_456_student_functions.py": b"print('test')"}))

    async def execute(*args, **kwargs):
        expire(run, monkeypatch)
        assert sweep()
        return GradingResult(success=True, score=100, max_score=100)

    from dispatch_helpers import drain
    from app.domains.runs.queue_admission import ticket_state
    # This fixture represents an unstarted upload, not a checkpointed result.
    (retention.workspace_root() / f"official_{run.id}" / "run_details.json").unlink(missing_ok=True)
    with patch("app.domains.grading.engine.GradingEngine.grade_submission", new=AsyncMock(side_effect=execute)):
        result = drain(run.id)
        assert result["failure_category"] == "review_expired"
        assert ticket_state(f"official:{run.id}") == "done"
    assert not (retention.workspace_root() / f"official_{run.id}").exists()
    assert "student_results" not in json.dumps(result)


def test_missing_heartbeat_and_overdue_failures_are_visible(run, monkeypatch):
    with SessionLocal() as db:
        assert not retention.health(db)["cleanup_service_healthy"]
        monkeypatch.setattr(retention, "utc_now", lambda: retention.deletion_deadline(run))
        assert retention.health(db)["cleanup_overdue_runs"] == 1
        retention.write_heartbeat(healthy=True, counts={})
        assert retention.health(db)["cleanup_service_healthy"]
        monkeypatch.setattr(retention, "utc_now", lambda: retention.deletion_deadline(run) + timedelta(minutes=4))
        assert not retention.health(db)["cleanup_service_healthy"]

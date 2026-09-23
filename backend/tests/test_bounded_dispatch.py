import csv
import json
import os
import subprocess
import sys
import zipfile
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select

from app.core.settings import get_settings
from app.db.base import Base
from app.db.session import SessionLocal
from app.domains.grading.engine import GradingResult
from app.domains.ingestion.engine import IngestError, SubmissionIngestionEngine
from app.domains.runs import retention
from app.domains.runs.dispatcher import sweep
from app.domains.runs.models import OfficialDispatch, RunSummary
from app.domains.runs.queue_admission import (
    QueueFullError, cancel_waiting, claim, release_execution_slots,
    reserve_execution_slots, ticket_state, waiting_count,
)
from app.domains.runs.service import official_run_dir, official_run_zip_path
from app.domains.runs.tasks import grade_official_run
from test_ingestion_extractor import create_zip_bytes


@pytest.fixture(autouse=True)
def environment(reset_database, tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    monkeypatch.setattr(settings, "sandbox_use_celery", True)
    monkeypatch.setattr(settings, "judge0_max_concurrent", 2)


def upload(count=1):
    archive = create_zip_bytes({f"synthetic_{10000+i}_{20000+i}_student_functions.py": b"print('synthetic')" for i in range(count)})
    with SessionLocal() as db:
        from app.domains.courses.models import Section
        section = db.scalar(select(Section).where(Section.crn == "12345"))
        run = SubmissionIngestionEngine().ingest_canvas_upload(db,
            course_id="cs1400", assignment_id="simple-python-functions",
            section_id=section.id, actor_user_id=1, filename="batch.zip", content=archive)
        return run.id


def delivery():
    messages = []
    sweep(lambda *args: messages.append(args))
    return messages


def test_200_submissions_are_individual_tasks_and_exports_survive_long_batch(monkeypatch):
    run_id = upload(200)
    assert waiting_count() == 0
    now = retention.utc_now()
    monkeypatch.setattr(retention, "utc_now", lambda: now)
    grader = AsyncMock(return_value=GradingResult(success=True, score=100, max_score=100))
    with patch("app.domains.grading.engine.GradingEngine.grade_submission", grader):
        for index in range(200):
            messages = delivery()
            assert len(messages) == 1
            outcome = grade_official_run(*messages[0])
            assert grader.call_count == index + 1
            assert "student_results" not in outcome
            assert outcome["state"] == ("complete" if index == 199 else "run")
            assert grade_official_run(*messages[0])["state"] == "ignored"
            now += timedelta(seconds=10)
    with SessionLocal() as db:
        run = db.get(RunSummary, run_id)
        assert run.success_count == 200 and run.status == "complete"
        assert run.failure_count == run.timeout_count == 0
    directory = official_run_dir(run_id)
    with (directory / "grades.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.reader(handle))) == 201
    with zipfile.ZipFile(directory / "feedback.zip") as archive:
        assert len(archive.namelist()) == 200
    assert waiting_count() == 0


def test_separate_intake_limits_and_no_execution_reservation():
    reserve_execution_slots(50)
    with pytest.raises(IngestError) as error:
        upload(201)
    assert error.value.status_code == 413
    for _ in range(5):
        upload(200)
    with pytest.raises(IngestError) as error:
        upload()
    assert error.value.status_code == 429
    assert delivery() == []
    assert waiting_count() == 50
    assert len(list(retention.workspace_root().glob("*.zip"))) == 5


def test_owned_release_cancel_duplicate_and_global_active_capacity():
    for owner in ("sandbox-a", "sandbox-b", "sandbox-c"):
        reserve_execution_slots(1, owner=owner)
    a = claim("sandbox-a")
    claim("sandbox-b")
    assert waiting_count() == 1
    assert claim("sandbox-a") is None
    assert not cancel_waiting("sandbox-a")
    with pytest.raises(QueueFullError):
        claim("sandbox-c")
    release_execution_slots(owner="sandbox-a", token="stale-token")
    assert ticket_state("sandbox-a") == "active"
    release_execution_slots(owner="sandbox-a", token=a)
    release_execution_slots(owner="sandbox-a", token=a)
    assert waiting_count() == 1
    assert claim("sandbox-c")


def test_broker_outage_and_delayed_deliveries_do_not_exhaust_attempts(monkeypatch):
    run_id = upload()
    now = retention.utc_now()
    monkeypatch.setattr(retention, "utc_now", lambda: now)
    messages = []

    def ambiguous_publish(*args):
        messages.append(args)
        raise ConnectionError("private transport details must not be stored")

    for _ in range(5):
        assert sweep(ambiguous_publish)["publish_failures"] == 1
        now += timedelta(seconds=61)
    current = delivery()[0]
    for message in messages:
        assert grade_official_run(*message)["state"] == "ignored"
    with patch("app.domains.grading.engine.GradingEngine.grade_submission", AsyncMock(return_value=GradingResult(success=True, score=100, max_score=100))):
        assert grade_official_run(*current)["state"] == "complete"
    with SessionLocal() as db:
        assert db.get(OfficialDispatch, run_id).attempts == 0


def test_crash_after_checkpoint_recovers_without_regrading(monkeypatch):
    run_id = upload()
    now = retention.utc_now()
    monkeypatch.setattr(retention, "utc_now", lambda: now)
    grader = AsyncMock(return_value=GradingResult(success=True, score=100, max_score=100))
    first = delivery()[0]
    with patch("app.domains.grading.engine.GradingEngine.grade_submission", grader):
        with patch("app.domains.runs.official_execution.write_run_grades_csv", side_effect=OSError("synthetic failure")):
            assert grade_official_run(*first)["failure_category"] == "execution_unavailable"
        now += timedelta(seconds=241)
        second = delivery()[0]
        assert second[1] != first[1]
        assert grade_official_run(*first)["state"] == "ignored"
        assert grade_official_run(*second)["state"] == "complete"
    assert grader.call_count == 1
    with SessionLocal() as db:
        assert db.get(RunSummary, run_id).success_count == 1


def test_worker_death_has_bounded_retries_and_retains_capacity_until_safe(monkeypatch):
    run_id = upload()
    now = retention.utc_now()
    monkeypatch.setattr(retention, "utc_now", lambda: now)
    for _ in range(3):
        message = delivery()[0]
        claim(f"official:{run_id}", message[1])  # Simulate process death after claim.
        now += timedelta(seconds=239)
        assert delivery() == []
        now += timedelta(seconds=2)
    assert delivery() == []
    with SessionLocal() as db:
        run = db.get(RunSummary, run_id)
        assert run.status == "failure"
        assert run.failure_summary == {"error": "execution_interrupted"}


def test_pending_and_active_expiry_never_recreate_workspace(monkeypatch):
    run_id = upload()
    message = delivery()[0]
    with SessionLocal() as db:
        deadline = retention.review_expiry(db.get(RunSummary, run_id))
    monkeypatch.setattr(retention, "utc_now", lambda: deadline)
    with SessionLocal() as db:
        retention.reconcile(db)
    assert delivery() == []
    assert grade_official_run(*message)["state"] == "ignored"
    assert not official_run_dir(run_id).exists()
    assert not official_run_zip_path(run_id).exists()


def test_manual_edit_during_next_submission_is_preserved():
    run_id = upload(2)
    async def execute(**kwargs):
        path = official_run_dir(run_id) / "run_details.json"
        with retention.access(run_id):
            payload = json.loads(path.read_text())
            if payload["student_results"]:
                next(iter(payload["student_results"].values()))["overall_comment"] = "Staff edit during execution"
                from app.domains.runs.service import write_run_details_json
                write_run_details_json(official_run_dir(run_id), payload)
        return GradingResult(success=True, score=100, max_score=100)
    with patch("app.domains.grading.engine.GradingEngine.grade_submission", AsyncMock(side_effect=execute)):
        grade_official_run(*delivery()[0])
        grade_official_run(*delivery()[0])
    payload = json.loads((official_run_dir(run_id) / "run_details.json").read_text())
    assert next(iter(payload["student_results"].values()))["overall_comment"] == "Staff edit during execution"


def test_database_outage_fails_closed():
    from sqlalchemy.exc import OperationalError
    with patch("app.domains.runs.queue_admission.SessionLocal", side_effect=OperationalError("private", {}, Exception())):
        with pytest.raises(HTTPException) as error:
            reserve_execution_slots(1, owner="sandbox")
    assert error.value.status_code == 503
    assert "private" not in error.value.detail


def test_round_robin_batches_leave_capacity_for_sandbox():
    ids = [upload(2) for _ in range(3)]
    messages = delivery()
    assert [message[0] for message in messages] == ids[:2]
    reserve_execution_slots(1, owner="sandbox-mixed")
    sandbox_token = claim("sandbox-mixed")
    assert sandbox_token
    assert claim(f"official:{ids[0]}", messages[0][1])
    with pytest.raises(QueueFullError):
        claim(f"official:{ids[1]}", messages[1][1])
    # Neither cancellation nor a duplicate can release the active official slot.
    assert not cancel_waiting(f"official:{ids[0]}")
    release_execution_slots(owner="sandbox-mixed", token=sandbox_token)
    from app.domains.runs.official_execution import step
    from app.domains.runs.dispatcher import finish_step
    with patch("app.domains.grading.engine.GradingEngine.grade_submission", AsyncMock(return_value=GradingResult(success=True, score=100, max_score=100))):
        step(*messages[0])
        finish_step(*messages[0])
    assert delivery()[0][0] == ids[2]


def test_dispatch_heartbeat_and_database_failure(monkeypatch):
    from app.domains.runs.dispatch_worker import heartbeat, healthy
    assert not healthy()
    heartbeat(True, {"published": 0, "publish_failures": 0})
    assert healthy()
    later = retention.utc_now() + timedelta(seconds=31)
    monkeypatch.setattr(retention, "utc_now", lambda: later)
    assert not healthy()
    heartbeat(False, {})
    assert not healthy()


def test_queued_delivery_can_wait_through_long_worker_outage(monkeypatch):
    run_id = upload()
    now = retention.utc_now()
    monkeypatch.setattr(retention, "utc_now", lambda: now)
    for _ in range(5):
        assert delivery()
        now += timedelta(seconds=61)
    with SessionLocal() as db:
        assert db.get(OfficialDispatch, run_id).attempts == 0
        assert db.get(RunSummary, run_id).status == "queue"


def test_scheduling_metadata_and_errors_do_not_copy_student_content(caplog):
    run_id = upload()
    messages = delivery()
    assert len(messages[0]) == 2 and messages[0][0] == run_id
    with patch("app.domains.runs.official_execution.step", side_effect=ValueError("synthetic_10000 private source print('synthetic')")):
        result = grade_official_run(*messages[0])
    with SessionLocal() as db:
        from app.domains.runs.models import ExecutionTicket
        run = db.get(RunSummary, run_id)
        ticket = db.get(ExecutionTicket, f"official:{run_id}")
        stored = json.dumps({"result": result, "failure": run.failure_summary,
            "owner": ticket.owner, "token": ticket.token})
    for forbidden in ("synthetic_10000", "private source", "print('synthetic')"):
        assert forbidden not in stored
        assert forbidden not in caplog.text


def test_cross_process_capacity_is_shared(tmp_path):
    url = f"sqlite+pysqlite:///{(tmp_path / 'capacity.db').as_posix()}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    script = """
import sys
from app.db.base import import_domain_models
import_domain_models()
from app.domains.runs.queue_admission import reserve_execution_slots, claim, QueueFullError
reserve_execution_slots(1, owner=sys.argv[1])
try:
    claim(sys.argv[1])
    print('active')
except QueueFullError:
    print('waiting')
"""
    env = {**os.environ, "DATABASE_URL": url, "ARTIFACT_STORAGE_DIR": str(tmp_path / "artifacts"), "JUDGE0_MAX_CONCURRENT": "2"}
    processes = [subprocess.Popen([sys.executable, "-c", script, f"opaque-{index}"],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for index in range(6)]
    try:
        outputs = [process.communicate(timeout=30) for process in processes]
        assert all(process.returncode == 0 for process in processes), outputs
        assert sum(out.strip() == "active" for out, _ in outputs) == 2
        assert sum(out.strip() == "waiting" for out, _ in outputs) == 4
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()

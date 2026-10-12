"""Synthetic official package admission, execution and recovery regressions."""
from __future__ import annotations

import json
import base64
import copy
import io
import zipfile
import subprocess
import sys
from datetime import timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.domains.courses.models import Section
from app.domains.assignments.service import get_assignment_for_course, save_artifact, upsert_assignment_config
from app.domains.ingestion.engine import IngestError, SubmissionIngestionEngine
from app.domains.runs import grading_package, retention
from app.domains.runs.dispatcher import sweep
from app.domains.runs.grading_package import GradingPackageError, PackageCaptureError, capture_package, load_package
from app.domains.runs.models import ExecutionTicket, OfficialDispatch, RunSummary
from app.domains.runs.service import official_run_dir, official_run_zip_path
from app.domains.runs.tasks import grade_official_run
from test_grading_executor import _mock_judge0_client
from test_ingestion_extractor import create_zip_bytes


@pytest.fixture(autouse=True)
def environment(reset_database, tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    monkeypatch.setattr(settings, "sandbox_use_celery", True)


def upload(count: int = 1) -> int:
    content = create_zip_bytes({
        f"synthetic_{10000 + i}_{20000 + i}_student_functions.py": b"print('synthetic')"
        for i in range(count)
    })
    with SessionLocal() as db:
        section = db.scalar(select(Section).where(Section.crn == "12345"))
        assert section is not None
        run = SubmissionIngestionEngine().ingest_canvas_upload(
            db, course_id="cs1400", assignment_id="simple-python-functions",
            section_id=section.id, actor_user_id=1, filename="synthetic.zip", content=content,
        )
        return run.id


def test_intake_persists_package_before_dispatch():
    run_id = upload()
    with SessionLocal() as db:
        dispatch = db.get(OfficialDispatch, run_id)
        assert dispatch is not None and dispatch.ready
    assert official_run_zip_path(run_id).is_file()
    snapshot = official_run_dir(run_id) / "grading_snapshot.json"
    assert snapshot.is_file(), "A dispatchable batch must already have its grading package"
    assert json.loads(snapshot.read_text(encoding="utf-8"))["version"] == 1


def test_grading_and_package_import_without_api_initialization():
    result = subprocess.run([
        sys.executable, "-c", "from app.domains.grading.engine import GradingEngine; "
        "from app.domains.runs.grading_package import capture_package; "
        "from scripts.validate_grading_package_host import verify",
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def delivery() -> tuple[int, str]:
    messages: list[tuple[int, str]] = []
    sweep(lambda *args: messages.append(args))
    assert len(messages) == 1
    return messages[0]


def test_every_submission_and_retry_uses_admitted_inputs(monkeypatch):
    with SessionLocal() as db:
        assignment = get_assignment_for_course(db, "cs1400", "simple-python-functions")
        config = copy.deepcopy(assignment.config.config)
        config["scoring_items"].append({"key": "manual_check", "label": "Original rubric",
                                     "points": 10, "extra_credit": False, "item_type": "manual"})
        upsert_assignment_config(db, assignment, config)
        db.commit()
    run_id = upload(2)
    with SessionLocal() as db:
        run = db.get(RunSummary, run_id)
        original = load_package(run_id, assignment_id=run.assignment_id)
        assignment = get_assignment_for_course(db, "cs1400", "simple-python-functions")
        config = copy.deepcopy(assignment.config.config)
        for item in config["scoring_items"]:
            item["label"] = "Changed after intake"
            item["points"] = 999
        config["description"] = "Changed instructions"
        assignment.description = "Changed instructions"
        assignment.course.default_concepts = ["unrelated_concept"]
        upsert_assignment_config(db, assignment, config)
        db.commit()
        for key, artifact in config["artifacts"].items():
            if artifact["type"] != "model_solution":
                save_artifact(db, "cs1400", "simple-python-functions", key, artifact["type"],
                              artifact["display_filename"], b"CHANGED_AFTER_ADMISSION")
    monkeypatch.setattr(get_settings(), "judge0_language_id", 999)
    monkeypatch.setattr(get_settings(), "test_execution_timeout_seconds", 1)
    monkeypatch.setattr(get_settings(), "judge0_preinstalled_dependencies", "")
    now = retention.utc_now()
    monkeypatch.setattr(retention, "utc_now", lambda: now)
    test_results = [{"nodeid": item.key, "outcome": "passed", "markers": [f"ag_{item.key}"],
                     "duration": 0.01} for item in original.config.scoring_items if item.item_type == "pytest"]
    client = _mock_judge0_client(submission_result={"status": {"id": 3}, "stdout": json.dumps(
        {"tests": test_results, "summary": {"exit_code": 0}})})
    from app.domains.runs import official_execution
    write_details = official_execution.write_run_details_json
    interrupted = False

    def crash_at_first_checkpoint(directory, details):
        nonlocal interrupted
        if details["student_results"] and not interrupted:
            interrupted = True
            raise OSError("synthetic interruption after execution")
        return write_details(directory, details)

    with patch("app.domains.grading.executor.create_judge0_client", return_value=client), \
         patch("app.domains.grading.executor.generate_runner_script", side_effect=AssertionError("live runner accessed")), \
         patch("app.domains.grading.engine.load_fallback_helper", side_effect=AssertionError("live helper accessed")), \
         patch.object(official_execution, "write_run_details_json", side_effect=crash_at_first_checkpoint):
        first = delivery()
        assert grade_official_run(*first)["state"] == "failure"
        now += timedelta(seconds=250)
        assert grade_official_run(*delivery())["state"] == "run"
        now += timedelta(seconds=10)
        assert grade_official_run(*delivery())["state"] == "complete"
        assert grade_official_run(*first)["state"] == "ignored"
    assert client.create_submission.await_count == client.delete_submission.await_count == 3
    for call in client.create_submission.await_args_list:
        kwargs = call.kwargs
        assert kwargs["source_code"] == original.runner_source
        assert kwargs["language_id"] == original.execution_parameters.language_id
        assert kwargs["cpu_time_limit"] == original.execution_parameters.cpu_time_limit
        assert kwargs["wall_time_limit"] == original.execution_parameters.wall_time_limit
        assert kwargs["memory_limit"] == original.execution_parameters.memory_limit
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(kwargs["additional_files_b64"]))) as files:
            for name, artifact in original.files.items():
                assert files.read(name) == artifact.decode()
            helper = original.files.get("python_autograder_helpers.py", original.fallback_helper)
            assert files.read("python_autograder_helpers.py") == helper.decode()
    details = json.loads((official_run_dir(run_id) / "run_details.json").read_text())
    for student in details["student_results"].values():
        assert student["score"] == sum(item.points for item in original.config.scoring_items
                                       if item.item_type == "pytest")
        assert student["manual_results"]["manual_check"]["label"] == "Original rubric"
        assert student["manual_results"]["manual_check"]["points"] == 10
    assert load_package(run_id, assignment_id=original.assignment_id).digest == original.digest


def test_binary_assets_are_captured_without_model_bytes_or_storage_paths():
    binary = b"\x00\xff\x80SYNTHETIC_BINARY"
    with SessionLocal() as db:
        assignment = get_assignment_for_course(db, "cs1400", "simple-python-functions")
        config = copy.deepcopy(assignment.config.config)
        config["artifacts"]["binary_support"] = {"type": "support_file", "display_filename": "asset.bin"}
        upsert_assignment_config(db, assignment, config)
        db.commit()
        save_artifact(db, "cs1400", "simple-python-functions", "binary_support", "support_file", "asset.bin", binary)
        for key, artifact in config["artifacts"].items():
            if artifact["type"] == "model_solution":
                save_artifact(db, "cs1400", "simple-python-functions", key, "model_solution",
                              artifact["display_filename"], b"UNIQUE_MODEL_SOLUTION_SECRET")
    package = capture_package("cs1400", "simple-python-functions")
    assert package.files["asset.bin"].decode() == binary
    assert all(b"UNIQUE_MODEL_SOLUTION_SECRET" not in file.decode() for file in package.files.values())
    serialized = package.model_dump_json()
    assert "file://" not in serialized and "seed://" not in serialized
    assert base64.b64encode(b"UNIQUE_MODEL_SOLUTION_SECRET").decode() not in serialized


@pytest.mark.parametrize("problem", ["missing", "hash", "type", "collision", "reserved"])
def test_capture_rejects_incomplete_or_conflicting_assets(problem):
    with SessionLocal() as db:
        assignment = get_assignment_for_course(db, "cs1400", "simple-python-functions")
        record = next(a for a in assignment.artifacts if a.artifact_type == "pytest_file")
        config = copy.deepcopy(assignment.config.config)
        if problem == "missing":
            record.storage_ref = "file://missing-synthetic-artifact"
        elif problem == "hash":
            record.sha256 = "0" * 64
        elif problem == "type":
            record.artifact_type = "support_file"
        elif problem == "reserved":
            config["artifacts"][record.artifact_key]["display_filename"] = "runner.py"
        else:
            config["artifacts"]["duplicate"] = {"type": "support_file",
                                               "display_filename": config["artifacts"][record.artifact_key]["display_filename"]}
            from app.domains.assignments.models import AssignmentArtifact
            db.add(AssignmentArtifact(assignment_id=assignment.id, artifact_key="duplicate",
                                     artifact_type="support_file", storage_ref=record.storage_ref))
        upsert_assignment_config(db, assignment, config)
        db.commit()
    with pytest.raises(PackageCaptureError):
        capture_package("cs1400", "simple-python-functions")
    with pytest.raises(IngestError) as error:
        upload()
    assert error.value.status_code == 400
    with SessionLocal() as db:
        assert db.scalar(select(RunSummary).where(RunSummary.workflow_type == "official")) is None


@pytest.mark.parametrize("tamper", ["missing", "version", "digest", "base64", "file_hash", "membership", "assignment"])
def test_invalid_package_fails_without_execution_or_exports(tamper):
    run_id = upload()
    path = official_run_dir(run_id) / "grading_snapshot.json"
    data = json.loads(path.read_text())
    if tamper == "missing":
        path.unlink()
    else:
        if tamper == "version":
            data["version"] = 2
        elif tamper == "digest":
            data["digest"] = "0" * 64
        elif tamper == "base64":
            next(iter(data["files"].values()))["content_base64"] = "!!!"
        elif tamper == "file_hash":
            next(iter(data["files"].values()))["sha256"] = "0" * 64
        elif tamper == "membership":
            data["pytest_filenames"] = []
        else:
            data["assignment_id"] += 100
        path.write_text(json.dumps(data))
    message = delivery()
    with patch("app.domains.grading.engine.execute_pytest_in_judge0") as execute:
        outcome = grade_official_run(*message)
    execute.assert_not_called()
    expected = "grading_package_missing" if tamper == "missing" else "grading_package_invalid"
    assert outcome["failure_category"] == expected
    with SessionLocal() as db:
        assert db.get(RunSummary, run_id).failure_summary == {"error": expected}
        assert db.get(ExecutionTicket, f"official:{run_id}").state == "done"
    assert not (official_run_dir(run_id) / "grades.csv").exists()
    assert not (official_run_dir(run_id) / "feedback.zip").exists()
    assert grade_official_run(*message)["state"] == "ignored"


@pytest.mark.parametrize("stage", ["zip_write", "zip_replace", "package_write", "package_replace", "ready_commit"])
def test_partial_admission_is_never_dispatchable(stage, monkeypatch):
    from pathlib import Path
    from sqlalchemy.orm import Session
    original_open, original_replace, original_commit = Path.open, Path.replace, Session.commit

    def fail_open(path, mode="r", *args, **kwargs):
        if mode == "wb" and ((stage == "zip_write" and path.name.endswith(".zip.tmp")) or
                             (stage == "package_write" and path.name == "grading_snapshot.json.tmp")):
            raise OSError("synthetic write failure")
        return original_open(path, mode, *args, **kwargs)

    def fail_replace(path, target):
        if ((stage == "zip_replace" and path.name.endswith(".zip.tmp")) or
                (stage == "package_replace" and path.name == "grading_snapshot.json.tmp")):
            raise OSError("synthetic replace failure")
        return original_replace(path, target)

    def fail_commit(db):
        if stage == "ready_commit" and any(isinstance(row, OfficialDispatch) and row.ready for row in db.dirty):
            raise OperationalError("", {}, Exception("synthetic unavailable commit"))
        return original_commit(db)

    monkeypatch.setattr(Path, "open", fail_open)
    monkeypatch.setattr(Path, "replace", fail_replace)
    monkeypatch.setattr(Session, "commit", fail_commit)
    with pytest.raises(IngestError) as error:
        upload()
    assert error.value.status_code == 500
    with SessionLocal() as db:
        run = db.scalar(select(RunSummary).where(RunSummary.workflow_type == "official"))
        assert run.status == "failure"
        assert not db.get(OfficialDispatch, run.id).ready
        assert not official_run_zip_path(run.id).exists()
        assert not official_run_dir(run.id).exists()
    messages = []
    sweep(lambda *args: messages.append(args))
    assert messages == []


def test_commit_applied_then_connection_failed_preserves_admission(monkeypatch):
    from sqlalchemy.orm import Session
    original_commit = Session.commit
    raised = False

    def uncertain_commit(db):
        nonlocal raised
        ready = any(isinstance(row, OfficialDispatch) and row.ready for row in db.dirty)
        original_commit(db)
        if ready and not raised:
            raised = True
            raise OperationalError("", {}, Exception("synthetic lost commit response"))

    monkeypatch.setattr(Session, "commit", uncertain_commit)
    run_id = upload()
    assert raised
    assert official_run_zip_path(run_id).exists()
    with SessionLocal() as db:
        run = db.get(RunSummary, run_id)
        assert run.status == "queue" and db.get(OfficialDispatch, run_id).ready
        load_package(run_id, assignment_id=run.assignment_id)


def test_unconfirmed_commit_keeps_files_for_reconciliation(monkeypatch):
    from app.domains.ingestion import engine as ingestion_module
    from sqlalchemy.orm import Session
    original_commit = Session.commit

    def unavailable():
        raise OperationalError("", {}, Exception("synthetic database outage"))

    def fail_commit(db):
        if any(isinstance(row, OfficialDispatch) and row.ready for row in db.dirty):
            monkeypatch.setattr(ingestion_module, "SessionLocal", unavailable)
            raise OperationalError("", {}, Exception("synthetic uncertain readiness"))
        return original_commit(db)

    monkeypatch.setattr(Session, "commit", fail_commit)
    with pytest.raises(IngestError) as error:
        upload()
    assert error.value.status_code == 503
    with SessionLocal() as db:
        run = db.scalar(select(RunSummary).where(RunSummary.workflow_type == "official"))
        assert not db.get(OfficialDispatch, run.id).ready
        assert official_run_zip_path(run.id).exists()
        assert (official_run_dir(run.id) / "grading_snapshot.json").exists()
    messages = []
    sweep(lambda *args: messages.append(args))
    assert messages == []


@pytest.mark.parametrize("effect", ["cache", "audit", "mock"])
def test_post_admission_effect_failure_does_not_delete_package(effect, monkeypatch):
    if effect == "mock":
        monkeypatch.setattr(get_settings(), "sandbox_use_celery", False)
    target = {"cache": "app.domains.ingestion.engine.set_run_state",
              "audit": "app.domains.ingestion.engine.audit_event",
              "mock": "app.domains.runs.tasks.run_mock_official_run"}[effect]
    with patch(target, side_effect=RuntimeError("synthetic unavailable effect")):
        run_id = upload()
    with SessionLocal() as db:
        run = db.get(RunSummary, run_id)
        assert run.status == "queue" and db.get(OfficialDispatch, run_id).ready
        load_package(run_id, assignment_id=run.assignment_id)
    assert official_run_zip_path(run_id).exists()


def test_mock_uses_frozen_manual_rubric_and_missing_package_fails():
    from app.domains.runs.mock_runner import run_mock_official_run
    run_id = upload()
    original = capture_package("cs1400", "simple-python-functions")
    with SessionLocal() as db:
        assignment = get_assignment_for_course(db, "cs1400", "simple-python-functions")
        config = copy.deepcopy(assignment.config.config)
        config["scoring_items"][0]["points"] = 999
        config["scoring_items"].append({"key": "late_manual", "label": "Added too late",
                                     "points": 10, "extra_credit": False, "item_type": "manual"})
        upsert_assignment_config(db, assignment, config)
        db.commit()
    run_mock_official_run(run_id)
    details = json.loads((official_run_dir(run_id) / "run_details.json").read_text())
    assert all(student["max_score"] == original.config.base_points and "late_manual" not in student["manual_results"]
               for student in details["student_results"].values())
    second = upload()
    (official_run_dir(second) / "grading_snapshot.json").unlink()
    run_mock_official_run(second)
    with SessionLocal() as db:
        assert db.get(RunSummary, second).failure_summary == {"error": "grading_package_missing"}
    assert not (official_run_dir(second) / "grades.csv").exists()


def test_snapshot_and_partial_files_expire_with_official_workspace(monkeypatch):
    run_id = upload()
    (official_run_dir(run_id) / "grading_snapshot.json.tmp").write_bytes(b"partial")
    (official_run_dir(run_id) / "official_archive.zip.tmp").write_bytes(b"partial")
    with SessionLocal() as db:
        run = db.get(RunSummary, run_id)
        monkeypatch.setattr(retention, "utc_now", lambda: retention.review_expiry(run))
        retention.reconcile(db)
        assert not official_run_dir(run_id).exists()
        assert not official_run_zip_path(run_id).exists()


def test_package_digest_covers_description_and_runtime():
    run_id = upload()
    path = official_run_dir(run_id) / "grading_snapshot.json"
    data = json.loads(path.read_text())
    data["description"] = "Changed after capture"
    data["execution_parameters"]["cpu_time_limit"] = 999.0
    path.write_text(json.dumps(data))
    with pytest.raises(GradingPackageError, match="grading_package_invalid"):
        load_package(run_id, assignment_id=data["assignment_id"])


@pytest.mark.parametrize("kind", ["instructor", "student", "fallback"])
def test_captured_helper_preserves_precedence(kind, tmp_path):
    from app.domains.grading.engine import GradingEngine
    with SessionLocal() as db:
        assignment = get_assignment_for_course(db, "cs1400", "simple-python-functions")
        config = copy.deepcopy(assignment.config.config)
        config["artifacts"] = {key: artifact for key, artifact in config["artifacts"].items()
                               if artifact.get("display_filename") != "python_autograder_helpers.py"}
        if kind == "instructor":
            config["artifacts"]["captured_helper"] = {"type": "support_file",
                                                     "display_filename": "python_autograder_helpers.py"}
        upsert_assignment_config(db, assignment, config)
        db.commit()
        if kind == "instructor":
            save_artifact(db, "cs1400", "simple-python-functions", "captured_helper", "support_file",
                          "python_autograder_helpers.py", b"INSTRUCTOR_HELPER")
    package = capture_package("cs1400", "simple-python-functions")
    bundle = tmp_path / "student_bundle"
    bundle.mkdir()
    (bundle / "student_functions.py").write_bytes(b"print('synthetic')")
    if kind in {"instructor", "student"}:
        (bundle / "python_autograder_helpers.py").write_bytes(b"STUDENT_HELPER")
    engine = GradingEngine(config=package.config, artifact_refs={}, allowed_concepts=package.concepts,
                           preloaded_artifacts=package.preloaded_artifacts(),
                           execution_parameters=package.execution_parameters,
                           runner_source=package.runner_source, fallback_helper=package.fallback_helper.decode())
    client = _mock_judge0_client()
    with patch("app.domains.grading.executor.create_judge0_client", return_value=client), \
         patch("app.domains.grading.engine.load_fallback_helper", side_effect=AssertionError("live helper accessed")):
        result = engine.grade_submission_sync(bundle_dir=bundle)
    assert result.success
    expected = {"instructor": b"INSTRUCTOR_HELPER", "student": b"STUDENT_HELPER",
                "fallback": package.fallback_helper.decode()}[kind]
    encoded = client.create_submission.await_args.kwargs["additional_files_b64"]
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as files:
        assert files.read("python_autograder_helpers.py") == expected


def test_sqlite_metadata_capture_has_one_read_snapshot(tmp_path, monkeypatch):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import Session
    from app.db.base import Base
    from app.domains.assignments.models import Assignment, AssignmentArtifact, AssignmentConfig
    from app.domains.courses.models import Course, Module
    # A private file DB lets a second connection commit between relationship reads.
    isolated = create_engine(f"sqlite+pysqlite:///{(tmp_path / 'snapshot.sqlite').as_posix()}")
    Base.metadata.create_all(isolated)
    with isolated.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL")
    with SessionLocal() as source, Session(isolated) as target:
        for model in (Course, Module, Assignment, AssignmentConfig, AssignmentArtifact):
            for row in source.scalars(select(model)):
                target.add(model(**{column.name: getattr(row, column.name) for column in model.__table__.columns}))
        target.commit()
    original = capture_package("cs1400", "simple-python-functions")
    changed = False

    def concurrent_edit(connection, cursor, statement, parameters, context, executemany):
        nonlocal changed
        if changed or not statement.startswith("SELECT assignments."):
            return
        changed = True
        with Session(isolated) as writer:
            assignment = get_assignment_for_course(writer, "cs1400", "simple-python-functions")
            assignment.course.default_concepts = ["concurrent_edit"]
            config = copy.deepcopy(assignment.config.config)
            config["scoring_items"][0]["points"] = 999
            upsert_assignment_config(writer, assignment, config)
            writer.commit()

    event.listen(isolated, "after_cursor_execute", concurrent_edit)
    monkeypatch.setattr(grading_package, "engine", isolated)
    try:
        captured = capture_package("cs1400", "simple-python-functions")
        assert changed
        assert captured.config == original.config
        assert captured.concepts == original.concepts
        subsequent = capture_package("cs1400", "simple-python-functions")
        assert subsequent.config != original.config
        assert subsequent.concepts != original.concepts
        assert "concurrent_edit" in subsequent.concepts
    finally:
        event.remove(isolated, "after_cursor_execute", concurrent_edit)
        isolated.dispose()

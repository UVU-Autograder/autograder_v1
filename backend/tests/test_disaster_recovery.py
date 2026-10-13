"""Tests for official grading-package rollout (#23) and disaster recovery (#27).

Verifies:
1. Isolated database metadata backup & restore produces zero schema drift and
   strictly excludes student run/submission tables (FERPA compliance).
2. Local AI service outage (ConnectError / TimeoutException) degrades gracefully
   without blocking or failing deterministic grading runs.
3. Rollout automation script (`scripts/rollout_grading_package.sh`) and runbook
   contracts in `docs/guides/workstation.md`.
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from unittest.mock import patch

import httpx
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base, import_domain_models
from app.domains.assignments.models import (
    Assignment,
    AssignmentConfig,
)
from app.domains.auth.models import Role, User
from app.domains.courses.models import Course, Module, Section
from app.domains.grading.engine import GradingResult
from app.domains.runs.models import RunSummary
from app.domains.sandbox.service import SandboxService
from app.domains.sandbox.store import InMemoryRunStateStore

REPO_ROOT = Path(__file__).resolve().parents[2]


def _extract_bash_metadata_tables(script_path: Path) -> list[str]:
    content = script_path.read_text(encoding="utf-8")
    match = re.search(r"METADATA_TABLES=\((.*?)\)", content, re.S)
    assert match is not None, "METADATA_TABLES array not found in backup_metadata.sh"
    return re.findall(r'"([^"]+)"', match.group(1))


def _extract_ps1_metadata_tables(script_path: Path) -> list[str]:
    content = script_path.read_text(encoding="utf-8")
    match = re.search(r"\$MetadataTables\s*=\s*@\((.*?)\)", content, re.S)
    assert match is not None, "$MetadataTables array not found in backup_metadata.ps1"
    return re.findall(r'"([^"]+)"', match.group(1))


def test_isolated_metadata_backup_restore_zero_schema_drift(tmp_path: Path) -> None:
    """Test metadata restore on an isolated database and verify zero schema drift (#27)."""
    import_domain_models()

    sh_tables = _extract_bash_metadata_tables(REPO_ROOT / "scripts" / "backup_metadata.sh")
    ps1_tables = _extract_ps1_metadata_tables(REPO_ROOT / "scripts" / "backup_metadata.ps1")
    assert sh_tables == ps1_tables, "Bash and PowerShell metadata table allowlists must match"

    allowlisted = set(sh_tables) - {"alembic_version"}
    all_orm_tables = set(Base.metadata.tables.keys())

    # Ephemeral/FERPA-sensitive tables must never be in the backup allowlist
    ephemeral_tables = {
        "run_summaries",
        "official_dispatches",
        "execution_tickets",
        "retention_leases",
        "retention_events",
    }
    assert allowlisted.isdisjoint(ephemeral_tables)
    assert allowlisted == (all_orm_tables - ephemeral_tables)

    # 1. Create source DB and populate persistent metadata + ephemeral run
    source_db_path = tmp_path / "source.db"
    restored_db_path = tmp_path / "restored.db"
    source_engine = create_engine(f"sqlite:///{source_db_path}")
    restored_engine = create_engine(f"sqlite:///{restored_db_path}")

    Base.metadata.create_all(source_engine)
    Base.metadata.create_all(restored_engine)

    SourceSession = sessionmaker(bind=source_engine)
    with SourceSession() as session:
        role = Role(name="instructor")
        user = User(email="instructor@uvu.edu", display_name="Dr. Test", is_active=True)
        course = Course(code="CS1400", title="Fundamentals of Programming", term="Fall 2026")
        session.add_all([role, user, course])
        session.flush()

        section = Section(
            course_id=course.id,
            crn="001",
            is_active=True,
        )
        module = Module(course_id=course.id, name="Module 1")
        session.add_all([section, module])
        session.flush()

        assignment = Assignment(
            course_id=course.id,
            module_id=module.id,
            slug="lab1-intro",
            title="Lab 1 Intro",
            description="Intro lab",
        )
        session.add(assignment)
        session.flush()

        config = AssignmentConfig(
            assignment_id=assignment.id,
            version=1,
            config={
                "version": "1.0",
                "required_files": ["main.py"],
                "scoring_items": [
                    {
                        "key": "test_main",
                        "label": "Main Test",
                        "points": 100,
                        "extra_credit": False,
                        "item_type": "pytest",
                    }
                ],
            },
        )
        ephemeral_run = RunSummary(
            assignment_id=assignment.id,
            section_id=section.id,
            workflow_type="official",
            status="complete",
            total_submission_count=25,
        )
        session.add_all([config, ephemeral_run])
        session.commit()

    # 2. Dump allowlisted metadata tables from source DB and restore into isolated target DB
    dumped_rows_by_table: dict[str, list[dict]] = {}
    with source_engine.connect() as src_conn:
        for table_name in sh_tables:
            if table_name == "alembic_version":
                continue
            tbl = Base.metadata.tables[table_name]
            rows = [dict(row._mapping) for row in src_conn.execute(tbl.select())]
            if rows:
                dumped_rows_by_table[table_name] = rows

    with restored_engine.begin() as dst_conn:
        for table_name, rows in dumped_rows_by_table.items():
            tbl = Base.metadata.tables[table_name]
            dst_conn.execute(tbl.insert(), rows)

    # 3. Verify zero schema drift between source and isolated restored DB
    source_inspector = inspect(source_engine)
    restored_inspector = inspect(restored_engine)
    assert set(source_inspector.get_table_names()) == set(restored_inspector.get_table_names())

    for table_name in source_inspector.get_table_names():
        src_cols = [
            (c["name"], str(c["type"]), c["nullable"])
            for c in source_inspector.get_columns(table_name)
        ]
        dst_cols = [
            (c["name"], str(c["type"]), c["nullable"])
            for c in restored_inspector.get_columns(table_name)
        ]
        assert src_cols == dst_cols, f"Schema drift detected on table {table_name}"
        assert (
            source_inspector.get_pk_constraint(table_name)["constrained_columns"]
            == restored_inspector.get_pk_constraint(table_name)["constrained_columns"]
        )

    # 4. Verify persistent metadata restored and ephemeral runs excluded
    RestoredSession = sessionmaker(bind=restored_engine)
    with RestoredSession() as restored_session:
        restored_course = restored_session.scalar(select(Course).where(Course.code == "CS1400"))
        assert restored_course is not None
        restored_assignment = restored_session.scalar(
            select(Assignment).where(Assignment.slug == "lab1-intro")
        )
        restored_config = restored_session.scalar(
            select(AssignmentConfig).where(AssignmentConfig.assignment_id == restored_assignment.id)
        )
        assert restored_config is not None
        assert restored_config.config["scoring_items"][0]["points"] == 100
        # FERPA boundary: ephemeral RunSummary rows must be 0 in restored DB
        assert restored_session.scalars(select(RunSummary)).all() == []

    source_engine.dispose()
    restored_engine.dispose()


def test_local_ai_outage_does_not_block_or_fail_grading_runs() -> None:
    """Confirm AI service interruption does not block or fail grading runs (#27)."""
    from app.domains.runs.schemas import QueueBackpressure

    store = InMemoryRunStateStore()
    service = SandboxService(use_celery=False, store=store)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("main.py", "def add(a, b):\n    return a - b\n")
    zip_bytes = buf.getvalue()

    config_dict = {
        "version": 1,
        "bundle": {
            "entrypoint": "main.py",
            "file_requirements": [{"label": "Main", "paths": ["main.py"]}],
        },
        "artifacts": {
            "test_main.py": {"type": "pytest_file"},
            "main.py": {"type": "model_solution"},
        },
        "scoring_items": [
            {
                "key": "item_add",
                "label": "Addition Check",
                "points": 50,
                "extra_credit": False,
                "item_type": "pytest",
            }
        ],
    }

    mock_grading_result = GradingResult(
        success=True,
        score=0,
        max_score=50,
        test_results=[
            {
                "key": "item_add",
                "label": "Addition Check",
                "points": 50,
                "points_awarded": 0,
                "passed": False,
                "test_results": [
                    {
                        "nodeid": "tests.py::test_add",
                        "outcome": "failed",
                        "message": "AssertionError: assert -1 == 5",
                        "failure_category": "assertion_failure",
                    }
                ],
            }
        ],
        warnings=[],
    )

    mock_bp = QueueBackpressure(
        current_waiting=0,
        high_load=False,
        accepting_runs=True,
    )

    with (
        patch(
            "app.domains.grading.engine.GradingEngine.grade_submission_sync",
            return_value=mock_grading_result,
        ),
        patch("app.domains.sandbox.service.reserve_execution_slots", return_value=1),
        patch("app.domains.sandbox.service.release_execution_slots"),
        patch("app.domains.runs.orchestrator.release_execution_slots"),
        patch("app.domains.sandbox.service.backpressure_snapshot", return_value=mock_bp),
    ):
        create_resp, session_id, err_code = service.create_run(
            course_id="cs1400",
            assignment_id="simple-addition",
            session_id=None,
            assignment_exists=True,
            max_score=50,
            zip_data=zip_bytes,
            config=config_dict,
            artifact_refs={},
            allowed_concepts=["functions"],
        )
        assert err_code is None
        assert create_resp is not None
        run_id = create_resp.run_id

        # Advance run through queue -> run -> complete
        service.get_status(run_id)
        service.get_status(run_id)

        # Simulate complete Local AI outage (ConnectError) during result + AI feedback fetch
        with patch(
            "httpx.Client.post",
            side_effect=httpx.ConnectError("Connection refused at 127.0.0.1:8001"),
        ):
            result_resp = service.get_result(run_id, session_id)
            assert result_resp is not None and result_resp != "not_ready"
            assert result_resp.state == "complete"
            assert result_resp.max_score == 50
            assert len(result_resp.test_summaries) == 1
            assert result_resp.test_summaries[0].status == "failed"

            ai_resp = service.generate_ai_feedback(run_id, session_id)
            assert ai_resp is not None
            assert "unreachable" in ai_resp.ai_feedback.lower()

            stream_chunks = list(service.generate_ai_feedback_stream(run_id, session_id) or [])
            assert "unreachable" in "".join(stream_chunks).lower()

        # Simulate Local AI timeout (TimeoutException)
        with patch(
            "httpx.Client.post",
            side_effect=httpx.TimeoutException("vLLM timed out"),
        ):
            ai_timeout_resp = service.generate_ai_feedback(run_id, session_id)
            assert ai_timeout_resp is not None
            assert "timed out" in ai_timeout_resp.ai_feedback.lower()


def test_rollout_grading_package_script_and_workstation_runbook_contracts() -> None:
    """Verify rollout automation script (#23) and workstation runbook sections (#23, #27)."""
    rollout_script = REPO_ROOT / "scripts" / "rollout_grading_package.sh"
    assert rollout_script.exists()
    script_text = rollout_script.read_text(encoding="utf-8")

    # Must check both RunSummary and ExecutionTicket before rebuilding
    assert "RunSummary" in script_text
    assert "ExecutionTicket" in script_text
    assert "backup_metadata.sh" in script_text
    assert "up -d --build backend celery-worker dispatch-worker cleanup-worker" in script_text
    assert "scripts/validate_grading_package_host.py" in script_text

    workstation_doc = (REPO_ROOT / "docs" / "guides" / "workstation.md").read_text(
        encoding="utf-8"
    )
    assert "## Official grading-package rollout and worker coordination" in workstation_doc
    assert "scripts/rollout_grading_package.sh" in workstation_doc
    assert "## Failure tolerance and disaster recovery runbook" in workstation_doc
    assert "Recovery Time Objective (RTO)" in workstation_doc
    assert "Recovery Point Objective (RPO)" in workstation_doc

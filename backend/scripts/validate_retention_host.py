"""Synthetic retention checks on the deployed database and shared local volume.

Run only during a drained maintenance window. This script never stops services;
the operator controls cleanup-worker, Redis, and PostgreSQL between phases. Only
rows tagged with this validation's random marker can be changed or removed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.settings import get_settings
from app.db.base import import_domain_models
from app.db.session import SessionLocal
from app.domains.assignments.models import Assignment
from app.domains.runs import retention
from app.domains.runs.models import RunSummary


class ValidationFailed(Exception):
    pass


def check(name: str, passed: bool) -> None:
    print(json.dumps({"check": name, "passed": bool(passed)}), flush=True)
    if not passed:
        raise ValidationFailed(name)


def save(path: Path, state: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state), encoding="utf-8")
    temporary.replace(path)


def paths(run_id: int) -> tuple[Path, Path]:
    root = retention.workspace_root()
    return root / f"official_{run_id}", root / f"official_{run_id}.zip"


def owned_run(db, state: dict, name: str) -> RunSummary:
    run = db.get(RunSummary, state["runs"][name], populate_existing=True)
    if run is None or run.failure_summary != {"retention_validation": state["marker"]}:
        raise ValidationFailed("synthetic_ownership_check")
    return run


def add_run(state: dict, state_path: Path, name: str, age: timedelta) -> int:
    if name in state["runs"]:
        raise ValidationFailed("fixture_already_exists")
    with SessionLocal() as db:
        run = RunSummary(
            workflow_type="official", assignment_id=state["assignment_id"],
            status="complete", total_submission_count=0,
            created_at=retention.utc_now() - age,
            failure_summary={"retention_validation": state["marker"]},
        )
        db.add(run)
        db.commit()
        run_id = run.id
    state["runs"][name] = run_id
    save(state_path, state)
    # Simulate files left from intake; never reuse an existing workspace.
    with retention.run_lock(run_id):
        directory, archive = paths(run_id)
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "run_details.json").write_text('{"student_results": {}}', encoding="utf-8")
        (directory / "grades.csv").write_text("score\n0\n", encoding="utf-8")
        for destination in (archive, directory / "feedback.zip"):
            with ZipFile(destination, "x") as package:
                package.writestr("synthetic.txt", "Synthetic retention validation only.")
    return run_id


def sentinel_paths(state: dict) -> list[Path]:
    marker = uuid.UUID(state["marker"]).hex
    root = retention.workspace_root()
    return [
        root / f"unknown_validation_{marker}",
        root / f"sandbox_validation_{marker}",
        get_settings().artifact_storage_path / f"instructor_validation_{marker}",
    ]


def verify_deleted(state: dict, name: str) -> None:
    run_id = state["runs"][name]
    with SessionLocal() as db:
        run = owned_run(db, state, name)
        check(f"{name}_durably_deleted", run.retention_state == "deleted" and run.deleted_at is not None)
        check(f"{name}_failure_cleared", run.cleanup_failure_category is None)
        check(f"{name}_original_deadlines", (
            retention.review_expiry(run) - retention.as_utc(run.created_at) == timedelta(hours=23)
            and retention.deletion_deadline(run) - retention.as_utc(run.created_at) == timedelta(hours=24)
        ))
    check(f"{name}_physically_absent", all(not os.path.lexists(p) for p in paths(run_id)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=(
        "prepare", "check-failure", "release-failure", "check-recovery",
        "prepare-outage", "check-outage", "check-outage-recovery", "finish",
    ))
    parser.add_argument("--assignment-id", type=int)
    parser.add_argument("--state-file", type=Path)
    args = parser.parse_args()
    if os.name != "posix" or os.geteuid() == 0:
        raise ValidationFailed("requires_nonroot_linux_backend_user")
    import_domain_models()
    retention.validate_root()
    state_path = args.state_file or retention.control_root() / "host-validation.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if args.phase == "prepare":
        if args.assignment_id is None:
            raise ValidationFailed("explicit_synthetic_assignment_required")
        with SessionLocal() as db:
            check("assignment_exists", db.get(Assignment, args.assignment_id) is not None)
        state = {"marker": str(uuid.uuid4()), "assignment_id": args.assignment_id, "runs": {}}
        with state_path.open("x", encoding="utf-8") as output:
            json.dump(state, output)
        add_run(state, state_path, "fresh", timedelta())
        add_run(state, state_path, "expired", timedelta(hours=23, minutes=2))
        failed_id = add_run(state, state_path, "failure", timedelta(hours=25))
        # Real permission failure under the same UID as cleanup-worker.
        paths(failed_id)[0].chmod(0o500)
        orphan_id = add_run(state, state_path, "orphan", timedelta(hours=25))
        with retention.run_lock(orphan_id), SessionLocal() as db:
            db.delete(owned_run(db, state, "orphan"))
            db.commit()
        for sentinel in sentinel_paths(state):
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            with sentinel.open("x", encoding="utf-8") as output:
                output.write("Synthetic sentinel; must survive official reconciliation.")
        check("fixtures_prepared", True)
        return

    state = json.loads(state_path.read_text(encoding="utf-8"))
    if args.phase == "check-failure":
        verify_deleted(state, "expired")
        with SessionLocal() as db:
            failed = owned_run(db, state, "failure")
            check("permission_failure_durable", failed.retention_state == "cleanup_failed")
            check("failure_sanitized", failed.cleanup_failure_category == "workspace_deletion_failed")
            check("failure_access_denied", not retention.available(failed))
            metrics = retention.health(db)
            check("failure_and_breach_visible", metrics["cleanup_failed_runs"] >= 1 and metrics["cleanup_overdue_runs"] >= 1)
            check("failure_unhealthy", not metrics["cleanup_service_healthy"])
            check("fresh_available", retention.available(owned_run(db, state, "fresh")))
        check("partial_deletion", paths(failed.id)[0].is_dir() and not paths(failed.id)[1].exists())
        check("fresh_files_preserved", all(p.exists() for p in paths(state["runs"]["fresh"])))
        check("orphan_removed", all(not os.path.lexists(p) for p in paths(state["runs"]["orphan"])))
        check("unrelated_files_preserved", all(p.is_file() for p in sentinel_paths(state)))
    elif args.phase == "release-failure":
        run_id = state["runs"]["failure"]
        with SessionLocal() as db:
            run = owned_run(db, state, "failure")
        with retention.run_lock(run_id):
            paths(run_id)[0].chmod(0o700)
        check("permission_restored", True)
    elif args.phase in ("check-recovery", "check-outage-recovery"):
        verify_deleted(state, "failure" if args.phase == "check-recovery" else "outage")
        with SessionLocal() as db:
            check("cleanup_healthy", retention.health(db)["cleanup_service_healthy"])
    elif args.phase == "prepare-outage":
        # Pause cleanup-worker before this phase to avoid racing the next sweep.
        add_run(state, state_path, "outage", timedelta(hours=25))
        check("outage_fixture_prepared", True)
    elif args.phase == "check-outage":
        # Deliberately avoid any database access while it is unavailable.
        check("database_outage_files_preserved", all(p.exists() for p in paths(state["runs"]["outage"])))
        heartbeat = json.loads((retention.control_root() / "heartbeat.json").read_text(encoding="utf-8"))
        check("database_outage_unhealthy", heartbeat["healthy"] is False)
        check("database_outage_report_recent", (
            retention.utc_now() - retention.as_utc(datetime.fromisoformat(heartbeat["checked_at"]))
        ).total_seconds() <= 180)
    elif args.phase == "finish":
        # Keep this validation's aggregate summaries; remove all synthetic files.
        with SessionLocal() as db:
            for name in state["runs"]:
                if name == "orphan":
                    continue
                run = owned_run(db, state, name)
                check(f"{name}_final_cleanup", retention.cleanup(run.id, db, manual=True))
        check("all_synthetic_official_files_absent", all(
            not os.path.lexists(p) for run_id in state["runs"].values() for p in paths(run_id)
        ))
        for sentinel in sentinel_paths(state):
            sentinel.unlink(missing_ok=True)
        state["completed_at"] = retention.utc_now().isoformat()
        save(state_path, state)
        check("validation_finished", True)


if __name__ == "__main__":
    try:
        main()
    except ValidationFailed as exc:
        raise SystemExit(f"Retention validation failed: {exc}") from None
    except Exception:
        # Filesystem/DB exceptions can contain paths or credentials. Never emit them.
        raise SystemExit("Retention validation failed: validation_operation_unavailable") from None

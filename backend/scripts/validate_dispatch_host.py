"""Synthetic Dell workload. Prints counts/timing only; retains an ownership manifest.

Invoke prepare, watch, and cleanup as separate phases so a disconnected SSH session
cannot orphan the workload. The cleanup phase deletes only the exact run created by
this script and verifies its ZIP and workspace are absent.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import httpx
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.settings import get_settings
from app.db.base import import_domain_models
from app.db.session import SessionLocal
from app.domains.auth.models import User
from app.domains.courses.models import Section
from app.domains.ingestion.engine import SubmissionIngestionEngine
from app.domains.runs import retention
from app.domains.runs.models import RunSummary
from app.domains.runs.service import official_run_dir, official_run_zip_path

import_domain_models()
MANIFEST = retention.control_root() / "dispatch_validation_manifest.json"
MODEL = Path(__file__).resolve().parents[1] / "app/db/seeds/simple-python-functions/model_solution.py"


def report(**values):
    print(json.dumps(values, sort_keys=True), flush=True)


def load_manifest():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    with SessionLocal() as db:
        run = db.get(RunSummary, manifest["run_id"])
        if not run or run.workflow_type != "official" or run.total_submission_count != manifest["count"]:
            raise RuntimeError("Validation run no longer matches its ownership manifest")
        created = retention.as_utc(run.created_at).isoformat()
        if created != manifest["created_at"]:
            raise RuntimeError("Validation run creation time does not match manifest")
    return manifest


def synthetic_zip(count):
    source = MODEL.read_bytes()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for index in range(count):
            archive.writestr(f"synthetic_{100000 + index}_{200000 + index}_student_functions.py", source)
    return buffer.getvalue()


def prepare(count):
    if MANIFEST.exists():
        raise RuntimeError("Previous validation manifest exists; inspect or clean it first")
    with SessionLocal() as db:
        staff = db.scalar(select(User).where(User.email == "dev.staff@uvu.edu"))
        section = db.scalar(select(Section).where(Section.crn == "12345"))
        if not staff or not section:
            raise RuntimeError("Synthetic seed staff or section unavailable")
        run = SubmissionIngestionEngine().ingest_canvas_upload(
            db, course_id="cs1400", assignment_id="simple-python-functions",
            section_id=section.id, actor_user_id=staff.id,
            filename="synthetic_canvas.zip", content=synthetic_zip(count),
        )
        manifest = {"run_id": run.id, "created_at": retention.as_utc(run.created_at).isoformat(),
            "count": count, "marker": str(uuid.uuid4()), "sandbox_run": None}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest), encoding="utf-8")
    temporary.replace(MANIFEST)
    report(phase="prepared", run_id=manifest["run_id"], count=count)


def submit_sandbox(manifest):
    if manifest["sandbox_run"] is not None:
        return manifest
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("student_functions.py", MODEL.read_bytes())
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10) as client:
        response = client.post("/sandbox/courses/cs1400/assignments/simple-python-functions/runs",
            files={"bundle": ("synthetic.zip", payload.getvalue(), "application/zip")})
        response.raise_for_status()
        body = response.json()
    manifest["sandbox_run"] = body["run_id"]
    manifest["sandbox_started_at"] = time.time()
    temporary = MANIFEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest), encoding="utf-8")
    temporary.replace(MANIFEST)
    report(phase="sandbox_submitted")
    return manifest


def check(manifest):
    with SessionLocal() as db:
        run = db.get(RunSummary, manifest["run_id"], populate_existing=True)
        if run is None:
            raise RuntimeError("Validation run is unavailable")
        completed = run.success_count + run.warning_count + run.failure_count + run.timeout_count
        data = {"state": run.status, "completed": completed, "total": run.total_submission_count,
            "success": run.success_count, "warnings": run.warning_count,
            "failed": run.failure_count, "timeouts": run.timeout_count,
            "packaging_seconds": run.export_packaging_seconds,
            "elapsed_seconds": round((datetime.now(UTC) - retention.as_utc(run.created_at)).total_seconds(), 2)}
    if data["state"] == "complete":
        with retention.access(manifest["run_id"]):
            directory = official_run_dir(manifest["run_id"])
            with (directory / "grades.csv").open(encoding="utf-8", newline="") as handle:
                import csv
                data["csv_rows"] = len(list(csv.reader(handle))) - 1
            with zipfile.ZipFile(directory / "feedback.zip") as archive:
                data["feedback_files"] = len(archive.namelist())
    report(phase="official_check", **data)
    return data


def sandbox_state(manifest):
    if manifest["sandbox_run"] is None:
        return None
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10) as client:
        response = client.get(f"/runs/{manifest['sandbox_run']}/status")
        response.raise_for_status()
        state = response.json()["state"]
    if state in ("complete", "failure"):
        elapsed = round(time.time() - manifest["sandbox_started_at"], 2)
        report(phase="sandbox_terminal", state=state, elapsed_seconds=elapsed)
        return state
    return None


def watch(manifest, *, timeout_seconds):
    start = time.monotonic()
    manifest = submit_sandbox(manifest)
    sandbox_done = False
    last_completed = -1
    while time.monotonic() - start < timeout_seconds:
        data = check(manifest)
        if data["completed"] != last_completed:
            last_completed = data["completed"]
        if manifest["sandbox_run"] and not sandbox_done:
            sandbox_done = sandbox_state(manifest) is not None
        if data["state"] in ("complete", "failure"):
            if not sandbox_done and manifest["sandbox_run"]:
                sandbox_done = sandbox_state(manifest) is not None
            if data["state"] == "complete" and not sandbox_done and manifest["sandbox_run"]:
                time.sleep(20)
                continue
            passed = (data["state"] == "complete" and data["completed"] == manifest["count"]
                and data["failed"] == 0 and data["timeouts"] == 0
                and data.get("csv_rows") == manifest["count"]
                and data.get("feedback_files") == manifest["count"]
                and data["elapsed_seconds"] < 2400
                and data["packaging_seconds"] is not None and data["packaging_seconds"] < 120
                and sandbox_done)
            report(phase="validated", passed=passed)
            if not passed:
                raise SystemExit(2)
            return
        time.sleep(20)
    raise TimeoutError("Synthetic run did not reach a terminal state within the limit")


def cleanup(manifest):
    with SessionLocal() as db:
        run = db.get(RunSummary, manifest["run_id"])
        if run is None:
            raise RuntimeError("Validation run is unavailable")
        if run.status in ("queue", "run"):
            raise RuntimeError("Cannot clean a queued or running validation run")
        if not retention.cleanup(run.id, db, manual=True):
            raise RuntimeError("Synthetic cleanup needs retry")
    if official_run_dir(manifest["run_id"]).exists() or official_run_zip_path(manifest["run_id"]).exists():
        raise RuntimeError("Synthetic official files remain")
    MANIFEST.unlink()
    report(phase="cleanup", physical_absence=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "check", "watch", "cleanup"))
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--timeout-seconds", type=int, default=2400)
    args = parser.parse_args()
    if args.phase == "prepare":
        if not get_settings().sandbox_use_celery:
            raise RuntimeError("Host validation requires Celery mode")
        prepare(args.count)
    else:
        manifest = load_manifest()
        if args.phase == "check":
            check(manifest)
        elif args.phase == "watch":
            watch(manifest, timeout_seconds=args.timeout_seconds)
        else:
            cleanup(manifest)


if __name__ == "__main__":
    main()

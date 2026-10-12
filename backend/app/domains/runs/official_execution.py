"""One official submission per invocation, with workspace-only checkpoints."""
import asyncio
import shutil
import time
from contextlib import contextmanager

from fastapi import HTTPException

from app.db.session import SessionLocal
from app.domains.grading.engine import GradingEngine, GradingResult
from app.domains.ingestion.extractor import group_canvas_files, parse_canvas_filename, prepare_student_bundle, safe_extract_zip
from app.domains.runs import retention
from app.domains.runs.feedback_formatter import generate_pedagogical_feedback_html
from app.domains.runs.grading_package import GradingPackageError, load_package
from app.domains.runs.models import ExecutionTicket
from app.domains.runs.queue_admission import transaction
from app.domains.runs.service import (
    init_manual_results, list_bundle_files, load_run_details_json, official_run_dir,
    official_run_zip_path, write_feedback_zip, write_run_details_json, write_run_grades_csv,
)


@contextmanager
def attempt_access(run_id: int, token: str):
    # Order is always run -> scheduler. The dispatcher never takes a run lock.
    with retention.access(run_id) as run:
        with transaction() as db:
            ticket = db.get(ExecutionTicket, f"official:{run_id}")
            if not ticket or ticket.token != token or ticket.state != "active" or retention.as_utc(ticket.expires_at) <= retention.utc_now():
                raise HTTPException(409, "Execution attempt is no longer current.")
        # Keep the run guard, but release scheduling authority before file reads.
        yield run


def step(run_id: int, token: str) -> dict:
    directory = official_run_dir(run_id)
    extracted = directory / "extracted"
    details_path = directory / "run_details.json"
    with attempt_access(run_id, token):
        with SessionLocal() as db:
            run = retention.load_run(db, run_id)
            if run.status in ("complete", "failure"):
                return {"run_id": run_id, "state": run.status}
            try:
                package = load_package(run_id, assignment_id=run.assignment_id)
            except GradingPackageError as exc:
                run.status = "failure"
                run.failure_summary = {"error": exc.category}
                db.commit()
                return {"run_id": run_id, "state": "failure", "failure_category": exc.category}
            run.status = "run"
            db.commit()
        config = package.config
        concepts = package.concepts
        preloaded = package.preloaded_artifacts()
        if not details_path.exists():
            safe_extract_zip(official_run_zip_path(run_id).read_bytes(), extracted)
            groups, unmatched = group_canvas_files(extracted)
            write_run_details_json(directory, {"unmatched_files": [p.name for p in unmatched],
                "student_results": {}, "run_status": "running"})
        else:
            groups, _ = group_canvas_files(extracted)
        if not groups:
            raise ValueError("submission_checkpoint_unavailable")
        details = load_run_details_json(details_path)
        remaining = [(key, paths) for key, paths in groups.items() if key not in details["student_results"]]
        selected = remaining[0] if remaining else None
        if selected:
            canvas_id, paths = selected
            parsed = next((parse_canvas_filename(p.name) for p in paths if parse_canvas_filename(p.name)), None)
            if parsed is None:
                raise ValueError("submission_unavailable")
            name, _, submission_id, _ = parsed
            bundle = directory / f"student_{canvas_id}"
            manual = init_manual_results(config.scoring_items)
            prepared = True
            try:
                if bundle.exists():
                    shutil.rmtree(bundle)
                bundle.mkdir()
                prepare_student_bundle(paths, bundle)
                files = list_bundle_files(bundle)
            except Exception:
                prepared, files = False, []

    # No locks span execution or network waits. Engine copies the input under
    # retention access and always cleans its separate execution workspace.
    if selected:
        automated_max = sum(item.points for item in config.scoring_items if item.item_type == "pytest" and not item.extra_credit)
        if prepared:
            engine = GradingEngine(config=config, artifact_refs={}, allowed_concepts=concepts,
                preloaded_artifacts=preloaded, execution_parameters=package.execution_parameters,
                runner_source=package.runner_source, fallback_helper=package.fallback_helper.decode())
            try:
                result = asyncio.run(engine.grade_submission(bundle_dir=bundle, official_run_id=run_id))
            except HTTPException:
                raise
            except Exception:
                result = GradingResult(success=False, max_score=config.base_points,
                    failure_category="internal_error", failure_message="Submission execution failed.")
        else:
            result = GradingResult(success=False, max_score=config.base_points,
                failure_category="preparation_error", failure_message="Submission bundle could not be prepared.")
        student = {"student_identifier": name, "submission_id": submission_id,
            "bundle_files": files, "bundle_file_count": len(files), "success": result.success,
            "score": result.score, "max_score": result.max_score, "automated_max_score": automated_max,
            "test_results": result.test_results, "warnings": [dict(w) for w in result.warnings],
            "failure_category": result.failure_category, "failure_message": result.failure_message,
            "feedback_html": generate_pedagogical_feedback_html(name, result, manual),
            "manual_results": manual, "overall_comment": ""}

    with attempt_access(run_id, token):
        # Reload to preserve manual grading performed while execution was in flight.
        details = load_run_details_json(details_path)
        results = details["student_results"]
        if selected:
            results.setdefault(canvas_id, student)
        complete = len(results) == len(groups)
        details["run_status"] = "complete" if complete else "running"
        write_run_details_json(directory, details)
        packaging_seconds = None
        if complete:
            packaging_start = time.perf_counter()
            write_run_grades_csv(directory, results)
            write_feedback_zip(directory, results)
            packaging_seconds = time.perf_counter() - packaging_start
        # Recompute from the atomic checkpoint, including after a crash between
        # filesystem replacement and DB commit. Never count a submission twice.
        successes = warnings = failures = timeouts = 0
        categories: dict[str, int] = {}
        for value in results.values():
            if value["success"]:
                if value["warnings"] or value["score"] < value["automated_max_score"]:
                    warnings += 1
                else:
                    successes += 1
            else:
                category = value.get("failure_category") or "unknown_failure"
                # Coarse allowlist: never persist grader exception text.
                if category not in {"timeout", "preparation_error", "internal_error", "validation_error", "execution_error"}:
                    category = "execution_error"
                categories[category] = categories.get(category, 0) + 1
                if category == "timeout":
                    timeouts += 1
                else:
                    failures += 1
        with SessionLocal() as db:
            run = retention.load_run(db, run_id)
            run.total_submission_count = len(groups)
            run.success_count, run.warning_count = successes, warnings
            run.failure_count, run.timeout_count = failures, timeouts
            run.failure_summary = categories
            if packaging_seconds is not None:
                run.export_packaging_seconds = packaging_seconds
            run.status = "complete" if complete else "run"
            db.commit()
        if complete and extracted.exists():
            shutil.rmtree(extracted)
    return {"run_id": run_id, "state": "complete" if complete else "run", "total": len(groups)}

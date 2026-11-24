"""One official submission per invocation, with workspace-only checkpoints."""
import asyncio
import shutil
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException

from app.db.session import SessionLocal
from app.domains.grading.engine import GradingEngine, GradingResult
from app.domains.grading.schemas import is_infrastructure_failure
from app.domains.ingestion.extractor import (
    detect_filename_collisions,
    group_canvas_files,
    parse_canvas_filename,
    prepare_student_bundle,
    safe_extract_zip,
)
from app.domains.runs import retention
from app.domains.runs.feedback_formatter import generate_pedagogical_feedback_html
from app.domains.runs.grading_package import GradingPackageError, load_package
from app.domains.runs.models import ExecutionTicket
from app.domains.runs.queue_admission import transaction
from app.domains.runs.service import (
    init_manual_results, list_bundle_files, load_checkpoint, load_run_details_json,
    official_run_dir, official_run_zip_path, write_checkpoint, write_run_details_json,
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


def _save_result(directory: Path, canvas_id: str, student: dict) -> dict:
    filename = f"graded-{canvas_id}.json"
    write_checkpoint(directory / filename, student)
    category = None
    if student["success"]:
        has_warning = student["warnings"] or student["score"] < student["automated_max_score"]
        outcome = "warning" if has_warning else "success"
    else:
        # Coarse allowlist: never persist grader exception text in operational metadata.
        category = student.get("failure_category")
        if category not in {"timeout", "preparation_error", "internal_error", "validation_error", "execution_error"}:
            category = "execution_error"
        outcome = "timeout" if category == "timeout" else "failure"
    return {"file": filename, "outcome": outcome, "category": category}


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
        details = load_run_details_json(details_path, include_students=False) if details_path.exists() else {}
        if not details:
            safe_extract_zip(official_run_zip_path(run_id).read_bytes(), extracted)
        if "roster" not in details:
            groups, unmatched = group_canvas_files(extracted)
            if not groups:
                raise ValueError("submission_checkpoint_unavailable")
            if not details:
                collisions = detect_filename_collisions(groups)
                unmatched_names = [p.name for p in unmatched]
                details = {
                    "unmatched_files": unmatched_names,
                    "filename_collisions": collisions,
                    "intake_acknowledged": not (unmatched_names or collisions),
                    "run_status": "running",
                }
            details["roster"] = {canvas_id: [p.name for p in paths] for canvas_id, paths in groups.items()}
            details["student_checkpoints"] = {
                canvas_id: _save_result(directory, canvas_id, student)
                for canvas_id, student in details.pop("student_results", {}).items()
            }
            write_run_details_json(directory, details)
        roster = details["roster"]
        canvas_id = next((key for key in roster if key not in details["student_checkpoints"]), None)
        checkpoint = directory / f"graded-{canvas_id}.json" if canvas_id is not None else None
        needs_execution = checkpoint is not None and not checkpoint.exists()
        if canvas_id is not None and needs_execution:
            if not extracted.exists():
                safe_extract_zip(official_run_zip_path(run_id).read_bytes(), extracted)
            paths = [extracted / name for name in roster[canvas_id]]
            parsed = parse_canvas_filename(paths[0].name)
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
    if canvas_id is not None and needs_execution:
        automated_max = sum(item.points for item in config.scoring_items if item.item_type == "pytest" and not item.extra_credit)
        if prepared:
            engine = GradingEngine(config=config, artifact_refs={}, allowed_concepts=concepts,
                preloaded_artifacts=preloaded, execution_parameters=package.execution_parameters,
                runner_source=package.runner_source, fallback_helper=package.fallback_helper.decode() if package.fallback_helper is not None else None,
                expected_manifest=package.expected_manifest.model_dump(mode="json"))
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
        infra_failed = not result.success and is_infrastructure_failure(result.failure_category)
        student = {"student_identifier": name, "submission_id": submission_id,
            "bundle_files": files, "bundle_file_count": len(files), "success": result.success,
            "score": None if infra_failed else result.score, "max_score": result.max_score, "automated_max_score": automated_max,
            "requires_adjudication": infra_failed,
            "test_results": result.test_results, "warnings": [dict(w) for w in result.warnings],
            "completion_objectives": [item.model_dump() for item in result.completion_objectives],
            "failure_category": result.failure_category, "failure_message": result.failure_message,
            "feedback_html": generate_pedagogical_feedback_html(name, result, manual, requires_adjudication=infra_failed),
            "manual_results": manual, "overall_comment": ""}
    elif checkpoint is not None:
        student = load_checkpoint(checkpoint)

    with attempt_access(run_id, token):
        # Reload to preserve manual grading performed while execution was in flight.
        details = load_run_details_json(details_path, include_students=False)
        results = details["student_checkpoints"]
        complete = len(results) + (canvas_id is not None) == len(roster)
        if canvas_id is not None:
            results[canvas_id] = _save_result(directory, canvas_id, student)
            details["run_status"] = "complete" if complete else "running"
            write_run_details_json(directory, details)
        # Recompute from the atomic checkpoint, including after a crash between
        # filesystem replacement and DB commit. Never count a submission twice.
        outcomes = {"success": 0, "warning": 0, "failure": 0, "timeout": 0}
        categories: dict[str, int] = {}
        for value in results.values():
            outcomes[value["outcome"]] += 1
            category = value["category"]
            if category:
                categories[category] = categories.get(category, 0) + 1
        with SessionLocal() as db:
            run = retention.load_run(db, run_id)
            run.total_submission_count = len(roster)
            run.success_count, run.warning_count = outcomes["success"], outcomes["warning"]
            run.failure_count, run.timeout_count = outcomes["failure"], outcomes["timeout"]
            run.failure_summary = categories
            run.status = "complete" if complete else "run"
            db.commit()
        if complete and extracted.exists():
            shutil.rmtree(extracted)
    return {"run_id": run_id, "state": "complete" if complete else "run", "total": len(roster)}

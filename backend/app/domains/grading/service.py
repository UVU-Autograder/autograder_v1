"""Grading service orchestrating AST checks, Judge0 execution, and scoring.

This service is the core pipeline for both sandbox and official grading runs.
It coordinates bundle validation, concept checking, workspace packaging,
Judge0 submission, result parsing, score calculation, and zero-retention cleanup.
"""
from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from app.core.settings import get_settings
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.executor import execute_pytest_in_judge0
from app.domains.grading.result_parser import PytestRunResult, calculate_scores
from app.domains.ingestion.extractor import (
    ExtractionError,
    safe_extract_zip,
    validate_submission_bundle,
)
from app.integrations.artifacts.resolver import load_artifact_content
from app.integrations.ast_checker.validator import ASTCheckResult, ASTFinding, check_student_code

logger = logging.getLogger(__name__)


@dataclass
class GradingResult:
    """Structured output of a grading run."""
    success: bool = False
    score: int = 0
    max_score: int = 0
    test_results: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    failure_category: str | None = None
    failure_message: str | None = None
    ast_result: ASTCheckResult | None = None
    pytest_result: PytestRunResult | None = None


async def run_grading_pipeline(
    zip_data: bytes,
    config: AssignmentConfigV1,
    artifact_refs: dict[str, str],
    allowed_concepts: list[str],
    stdin: str | None = None,
) -> GradingResult:
    """Execute the full grading pipeline for a single submission.

    :param stdin: Optional raw stdin text string passed to the execution environment.

    Steps:
    1. Extract ZIP to ephemeral workspace
    2. Validate bundle structure against config
    3. AST concept checking
    4. Add assignment artifacts
    5. Submit to Judge0 and poll for results
    6. Delete Judge0 submission (zero-retention)
    7. Parse results and calculate scores
    8. Clean up ephemeral workspace
    """
    settings = get_settings()
    workspace = Path(tempfile.mkdtemp(prefix="ag_grade_"))
    result = GradingResult(max_score=config.base_points)

    try:
        # Extract, validate, and AST-check in one directory (no student→exec copy).
        exec_dir = workspace / "execution"
        try:
            safe_extract_zip(zip_data, exec_dir)
        except ExtractionError as exc:
            result.failure_category = "unsafe_zip"
            result.failure_message = str(exc)
            return result

        try:
            validate_submission_bundle(exec_dir, config)
        except ValueError as exc:
            category = "missing_required_file"
            msg = str(exc)
            if "entrypoint" in msg.lower():
                category = "ambiguous_entrypoint"
            result.failure_category = category
            result.failure_message = msg
            return result

        # Collect and scan all student Python files in the submission
        student_py_files = sorted([
            f for f in exec_dir.rglob("*.py")
            if f.is_file()
        ])

        combined_detected = set()
        combined_warnings = []
        combined_blocked = []

        for py_file in student_py_files:
            rel_path = py_file.relative_to(exec_dir)
            try:
                source_code = py_file.read_text(encoding="utf-8")
            except Exception as exc:
                result.failure_category = "validation_error"
                result.failure_message = f"Could not read file {rel_path}: {exc}"
                return result

            ast_res = check_student_code(source_code, allowed_concepts)
            combined_detected.update(ast_res.detected_concepts)

            for warning in ast_res.warnings:
                combined_warnings.append(
                    ASTFinding(
                        code=warning.code,
                        message=f"[{rel_path.as_posix()}] {warning.message}",
                        line=warning.line,
                    )
                )
            for blocked_item in ast_res.blocked:
                combined_blocked.append(
                    ASTFinding(
                        code=blocked_item.code,
                        message=f"[{rel_path.as_posix()}] {blocked_item.message}",
                        line=blocked_item.line,
                    )
                )

        ast_result = ASTCheckResult(
            detected_concepts=combined_detected,
            warnings=combined_warnings,
            blocked=combined_blocked,
        )
        result.ast_result = ast_result

        for finding in ast_result.warnings:
            result.warnings.append({"code": finding.code, "message": finding.message})

        if ast_result.is_blocked:
            result.failure_category = "concept_blocked"
            blocked_msgs = [f.message for f in ast_result.blocked]
            result.failure_message = "; ".join(blocked_msgs)
            return result

        test_filenames: list[str] = []
        for artifact_key, storage_ref in artifact_refs.items():
            artifact_config = config.artifacts.get(artifact_key)
            if artifact_config is None:
                continue

            if artifact_config.type == "model_solution":
                continue

            try:
                content = load_artifact_content(storage_ref)
            except (FileNotFoundError, ValueError) as exc:
                logger.warning("Could not load artifact %s: %s", artifact_key, exc)
                continue

            filename = artifact_config.display_filename or artifact_key
            (exec_dir / filename).write_bytes(content)

            if artifact_config.type == "pytest_file":
                test_filenames.append(filename)

        # Auto-inject universal python_autograder_helpers.py if not present
        helpers_target = exec_dir / "python_autograder_helpers.py"
        if not helpers_target.exists():
            shared_helpers = Path(__file__).resolve().parents[2] / "db" / "seeds" / "shared" / "python_autograder_helpers.py"
            if shared_helpers.exists():
                helpers_target.write_bytes(shared_helpers.read_bytes())

        if not test_filenames:
            result.failure_category = "validation_error"
            result.failure_message = "No pytest file artifacts found for this assignment."
            return result

        test_cases_map: dict[str, dict[str, list[str]]] = {}
        for test in config.scoring_items:
            if test.inputs is not None and test.outputs is not None:
                test_cases_map[test.key] = {
                    "inputs": test.inputs,
                    "outputs": test.outputs,
                }

        outcome = await execute_pytest_in_judge0(
            exec_dir,
            test_filenames=test_filenames,
            test_cases=test_cases_map,
            entrypoint_module=Path(config.bundle.entrypoint).stem,
            language_id=settings.judge0_language_id,
            cpu_time_limit=float(settings.test_execution_timeout_seconds),
            dependencies=config.dependencies,
            stdin=stdin,
        )

        result.pytest_result = outcome.pytest_result
        if not outcome.success:
            result.failure_category = outcome.failure_category
            result.failure_message = outcome.failure_message
            return result

        assert outcome.pytest_result is not None
        score, test_details = calculate_scores(outcome.pytest_result, config.scoring_items)
        result.score = score
        result.test_results = test_details
        result.success = True

    finally:
        shutil.rmtree(workspace, ignore_errors=True)

    return result

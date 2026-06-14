"""Grading service orchestrating AST checks, Judge0 execution, and scoring.

This service is the core pipeline for both sandbox and official grading runs.
It coordinates bundle validation, concept checking, workspace packaging,
Judge0 submission, result parsing, score calculation, and zero-retention cleanup.
"""
from __future__ import annotations

import base64
import io
import logging
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from app.core.settings import get_settings
from app.domains.assignments.schemas import AssignmentConfigV1, pytest_marker_for_key
from app.domains.grading.result_parser import (
    PytestRunResult,
    calculate_scores,
    parse_pytest_json,
)
from app.domains.grading.runner_gen import generate_runner_script
from app.domains.ingestion.extractor import safe_extract_zip, validate_submission_bundle
from app.integrations.artifacts.resolver import load_artifact_content
from app.integrations.ast_checker.validator import ASTCheckResult, check_student_code

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
) -> GradingResult:
    """Execute the full grading pipeline for a single submission.

    Steps:
    1. Extract ZIP to ephemeral workspace
    2. Validate bundle structure against config
    3. AST concept checking
    4. Package workspace for Judge0
    5. Submit to Judge0 and poll for results
    6. Delete Judge0 submission (zero-retention)
    7. Parse results and calculate scores
    8. Clean up ephemeral workspace

    Args:
        zip_data: Raw ZIP file bytes of the student submission.
        config: Validated assignment configuration.
        artifact_refs: Map of artifact_key -> storage_ref for assignment artifacts.
        allowed_concepts: Merged effective concept whitelist.

    Returns:
        GradingResult with scores, test results, and any warnings/failures.
    """
    settings = get_settings()
    workspace = Path(tempfile.mkdtemp(prefix="ag_grade_"))
    result = GradingResult(max_score=config.base_points)

    try:
        # --- Step 1: Extract student submission ---
        student_dir = workspace / "student"
        try:
            safe_extract_zip(zip_data, student_dir)
        except Exception as exc:
            result.failure_category = "unsafe_zip"
            result.failure_message = str(exc)
            return result

        # --- Step 2: Validate bundle structure ---
        try:
            validate_submission_bundle(student_dir, config)
        except ValueError as exc:
            category = "missing_required_file"
            msg = str(exc)
            if "entrypoint" in msg.lower():
                category = "ambiguous_entrypoint"
            result.failure_category = category
            result.failure_message = msg
            return result

        # --- Step 3: AST concept checking ---
        entrypoint_path = student_dir / config.bundle.entrypoint
        try:
            source_code = entrypoint_path.read_text(encoding="utf-8")
        except Exception as exc:
            result.failure_category = "validation_error"
            result.failure_message = f"Could not read entrypoint: {exc}"
            return result

        ast_result = check_student_code(source_code, allowed_concepts)
        result.ast_result = ast_result

        # Add concept warnings
        for finding in ast_result.warnings:
            result.warnings.append({"code": finding.code, "message": finding.message})

        # Block execution if security violations found
        if ast_result.is_blocked:
            result.failure_category = "concept_blocked"
            blocked_msgs = [f.message for f in ast_result.blocked]
            result.failure_message = "; ".join(blocked_msgs)
            return result

        # --- Step 4: Package workspace for Judge0 ---
        exec_dir = workspace / "execution"
        exec_dir.mkdir(parents=True)

        # Copy student files into execution directory
        for item in student_dir.rglob("*"):
            if item.is_file():
                dest = exec_dir / item.relative_to(student_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

        # Copy assignment artifacts (pytest files, support files)
        test_filenames: list[str] = []
        for artifact_key, storage_ref in artifact_refs.items():
            artifact_config = config.artifacts.get(artifact_key)
            if artifact_config is None:
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

        if not test_filenames:
            result.failure_category = "validation_error"
            result.failure_message = "No pytest file artifacts found for this assignment."
            return result

        # Generate runner.py
        runner_source = generate_runner_script(test_filenames)
        (exec_dir / "runner.py").write_text(runner_source, encoding="utf-8")

        # Create additional_files ZIP
        additional_zip_buffer = io.BytesIO()
        with zipfile.ZipFile(additional_zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in exec_dir.rglob("*"):
                if item.is_file() and item.name != "runner.py":
                    arcname = str(item.relative_to(exec_dir))
                    zf.write(item, arcname)
        additional_files_b64 = base64.b64encode(additional_zip_buffer.getvalue()).decode("ascii")

        # --- Step 5: Submit to Judge0 ---
        from app.integrations.judge0.client import (
            Judge0CleanupError,
            Judge0Error,
            create_judge0_client,
        )

        judge0 = create_judge0_client()
        token: str | None = None
        try:
            token = await judge0.create_submission(
                source_code=runner_source,
                language_id=settings.judge0_language_id,
                additional_files_b64=additional_files_b64,
                cpu_time_limit=float(settings.test_execution_timeout_seconds),
                memory_limit=262144,
            )

            submission_result = await judge0.poll_submission(token)

            # --- Step 6: Parse results ---
            stdout = submission_result.get("stdout", "") or ""
            stderr = submission_result.get("stderr", "") or ""
            status_id = submission_result.get("status", {}).get("id", 0)

            # Check for Judge0-level failures
            if status_id == 5:  # Time Limit Exceeded
                result.failure_category = "timeout"
                result.failure_message = "Execution timed out."
                return result
            elif status_id == 6:  # Compilation Error
                result.failure_category = "compile_error"
                result.failure_message = "Code could not be compiled or imported."
                return result
            elif status_id >= 7 and status_id <= 12:  # Runtime errors
                result.failure_category = "test_failure"
                result.failure_message = "Runtime error during execution."
                return result
            elif status_id == 13:  # Internal Error
                result.failure_category = "judge0_error"
                result.failure_message = "Execution engine internal error."
                return result

            # Parse pytest JSON output
            pytest_result = parse_pytest_json(stdout)
            result.pytest_result = pytest_result

            if pytest_result.error_message:
                result.failure_category = "test_failure"
                result.failure_message = pytest_result.error_message
                return result

            # --- Step 7: Calculate scores ---
            score, test_details = calculate_scores(pytest_result, config.tests)
            result.score = score
            result.test_results = test_details
            result.success = True

        except Judge0Error as exc:
            result.failure_category = "judge0_error"
            result.failure_message = str(exc)
            return result

        finally:
            # --- Zero-retention cleanup: delete Judge0 submission ---
            if token is not None:
                try:
                    await judge0.delete_submission(token)
                except Judge0CleanupError:
                    logger.error(
                        "CLEANUP FAILURE: Could not delete Judge0 submission %s. "
                        "This is a launch-blocking violation of the zero-retention contract.",
                        token,
                    )
                    result.failure_category = "cleanup_failure"
                    result.failure_message = (
                        "Judge0 submission cleanup failed. "
                        "This is a zero-retention violation."
                    )
                    result.success = False

    finally:
        # --- Step 8: Clean up ephemeral workspace ---
        try:
            shutil.rmtree(workspace, ignore_errors=True)
        except Exception:
            logger.error("Failed to clean up workspace %s", workspace)

    return result

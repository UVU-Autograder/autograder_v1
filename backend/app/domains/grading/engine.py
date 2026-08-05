"""Grading engine module managing submission intake, AST inspection, Judge0 execution, and zero-retention cleanup.

This module provides the deep `GradingEngine` class, encapsulating workspace creation,
ZIP extraction, bundle validation, AST concept checking, artifact injection,
Judge0 pytest runner invocation, scoring, and zero-retention filesystem wipes.
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
from app.integrations.ast_checker.validator import ASTCheckResult, ASTCodeInspector, ASTFinding

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


class GradingEngine:
    """Deep domain engine for executing Python submission grading.

    Encapsulates submission extraction, AST policy inspection, helper script injection,
    Judge0 execution, score calculation, and zero-retention workspace cleanup.
    """

    def __init__(
        self,
        config: AssignmentConfigV1,
        artifact_refs: dict[str, str],
        allowed_concepts: list[str],
    ) -> None:
        self.config = config
        self.artifact_refs = artifact_refs
        self.allowed_concepts = allowed_concepts
        self.settings = get_settings()

    async def grade_submission(
        self,
        zip_data: bytes,
        stdin: str | None = None,
    ) -> GradingResult:
        """Execute the full grading pipeline for a single student submission bundle.

        :param zip_data: Raw byte array of the student submission ZIP archive.
        :param stdin: Optional raw stdin text passed to the execution environment.
        :return: Structured GradingResult containing score, test details, and failure reasons.
        """
        workspace = Path(tempfile.mkdtemp(prefix="ag_grade_"))
        result = GradingResult(max_score=self.config.base_points)

        try:
            exec_dir = workspace / "execution"
            try:
                safe_extract_zip(zip_data, exec_dir)
            except ExtractionError as exc:
                result.failure_category = "unsafe_zip"
                result.failure_message = str(exc)
                return result

            try:
                validate_submission_bundle(exec_dir, self.config)
            except ValueError as exc:
                category = "missing_required_file"
                msg = str(exc)
                if "entrypoint" in msg.lower():
                    category = "ambiguous_entrypoint"
                result.failure_category = category
                result.failure_message = msg
                return result

            # Audit submission directory using ASTCodeInspector
            inspector = ASTCodeInspector(allowed_concepts=self.allowed_concepts)
            ast_result = inspector.inspect_directory(exec_dir)
            result.ast_result = ast_result

            for finding in ast_result.warnings:
                result.warnings.append({"code": finding.code, "message": finding.message})

            if ast_result.is_blocked:
                result.failure_category = "concept_blocked"
                blocked_msgs = [f.message for f in ast_result.blocked]
                result.failure_message = "; ".join(blocked_msgs)
                return result

            test_filenames: list[str] = []
            for artifact_key, storage_ref in self.artifact_refs.items():
                artifact_config = self.config.artifacts.get(artifact_key)
                if artifact_config is None:
                    continue

                if artifact_config.type == "model_solution":
                    continue

                try:
                    content = load_artifact_content(storage_ref)
                except (FileNotFoundError, ValueError) as exc:
                    logger.warning("Could not load artifact %s: %s", artifact_key, exc)
                    continue

                raw_filename = artifact_config.display_filename or artifact_key
                filename = Path(raw_filename).name
                (exec_dir / filename).write_bytes(content)

                if artifact_config.type == "pytest_file":
                    test_filenames.append(filename)

            # Auto-inject universal python_autograder_helpers.py if not present
            helpers_target = exec_dir / "python_autograder_helpers.py"
            if not helpers_target.exists():
                domain_helpers = Path(__file__).resolve().parent / "resources" / "python_autograder_helpers.py"
                shared_helpers = Path(__file__).resolve().parents[2] / "db" / "seeds" / "shared" / "python_autograder_helpers.py"
                source_path = domain_helpers if domain_helpers.exists() else shared_helpers
                if source_path.exists():
                    helpers_target.write_bytes(source_path.read_bytes())

            if not test_filenames:
                result.failure_category = "validation_error"
                result.failure_message = "No pytest file artifacts found for this assignment."
                return result

            test_cases_map: dict[str, dict[str, list[str]]] = {}
            for test in self.config.scoring_items:
                if test.inputs is not None and test.outputs is not None:
                    test_cases_map[test.key] = {
                        "inputs": test.inputs,
                        "outputs": test.outputs,
                    }

            outcome = await execute_pytest_in_judge0(
                exec_dir,
                test_filenames=test_filenames,
                test_cases=test_cases_map,
                entrypoint_module=Path(self.config.bundle.entrypoint).stem,
                language_id=self.settings.judge0_language_id,
                cpu_time_limit=float(self.settings.test_execution_timeout_seconds),
                dependencies=self.config.dependencies,
                stdin=stdin,
            )

            result.pytest_result = outcome.pytest_result
            if not outcome.success:
                result.failure_category = outcome.failure_category
                result.failure_message = outcome.failure_message
                return result

            assert outcome.pytest_result is not None
            score, test_details = calculate_scores(outcome.pytest_result, self.config.scoring_items)
            result.score = score
            result.test_results = test_details
            result.success = True

        finally:
            shutil.rmtree(workspace, ignore_errors=True)

        return result

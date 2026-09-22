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
from app.integrations.ast_checker.validator import (
    ASTCheckResult,
    ASTCodeInspector,
)

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

    def to_dict(self, run_id: str | None = None) -> dict:
        """Serialize GradingResult into a standardized dictionary for state tracking and Redis."""
        data = {
            "success": self.success,
            "score": self.score,
            "max_score": self.max_score,
            "test_results": self.test_results,
            "warnings": self.warnings,
            "failure_category": self.failure_category,
            "failure_message": self.failure_message,
        }
        if run_id is not None:
            data["run_id"] = run_id
        return data


@dataclass(frozen=True)
class PreloadedArtifacts:
    """Assignment artifacts loaded once per official run."""

    files: dict[str, bytes]
    pytest_filenames: list[str]


def preload_grading_artifacts(
    config: AssignmentConfigV1,
    artifact_refs: dict[str, str],
) -> PreloadedArtifacts:
    """Load non-model-solution artifact bytes once for reuse across students."""
    files: dict[str, bytes] = {}
    pytest_filenames: list[str] = []
    for artifact_key, storage_ref in artifact_refs.items():
        artifact_config = config.artifacts.get(artifact_key)
        if artifact_config is None or artifact_config.type == "model_solution":
            continue
        try:
            content = load_artifact_content(storage_ref)
        except (FileNotFoundError, ValueError) as exc:
            logger.warning("Could not preload artifact %s: %s", artifact_key, exc)
            continue
        filename = Path(artifact_config.display_filename or artifact_key).name
        files[filename] = content
        if artifact_config.type == "pytest_file":
            pytest_filenames.append(filename)
    return PreloadedArtifacts(files=files, pytest_filenames=pytest_filenames)


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
        preloaded_artifacts: PreloadedArtifacts | None = None,
    ) -> None:
        self.config = config
        self.artifact_refs = artifact_refs
        self.allowed_concepts = allowed_concepts
        self.preloaded_artifacts = preloaded_artifacts
        self.settings = get_settings()

    def grade_submission_sync(
        self,
        zip_data: bytes | None = None,
        *,
        bundle_dir: Path | None = None,
        stdin: str | None = None,
    ) -> GradingResult:
        """Synchronous convenience entrypoint for Celery workers and offline execution."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import nest_asyncio  # type: ignore[import-not-found]

            nest_asyncio.apply()
            return loop.run_until_complete(
                self.grade_submission(zip_data, bundle_dir=bundle_dir, stdin=stdin)
            )
        return asyncio.run(
            self.grade_submission(zip_data, bundle_dir=bundle_dir, stdin=stdin)
        )

    async def grade_submission(
        self,
        zip_data: bytes | None = None,
        *,
        bundle_dir: Path | None = None,
        stdin: str | None = None,
    ) -> GradingResult:
        """Execute the full grading pipeline for a single student submission bundle.

        Provide exactly one of ``zip_data`` or ``bundle_dir``.
        """
        if (zip_data is None) == (bundle_dir is None):
            raise ValueError("Provide exactly one of zip_data or bundle_dir")

        workspace = Path(tempfile.mkdtemp(prefix="ag_grade_"))
        result = GradingResult(max_score=self.config.base_points)

        try:
            exec_dir = workspace / "execution"
            if bundle_dir is not None:
                shutil.copytree(bundle_dir, exec_dir)
            else:
                assert zip_data is not None
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

            test_filenames = self._inject_artifacts(exec_dir)

            helpers_target = exec_dir / "python_autograder_helpers.py"
            if not helpers_target.exists():
                domain_helpers = (
                    Path(__file__).resolve().parent / "resources" / "python_autograder_helpers.py"
                )
                shared_helpers = (
                    Path(__file__).resolve().parents[2]
                    / "db"
                    / "seeds"
                    / "shared"
                    / "python_autograder_helpers.py"
                )
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

    def _inject_artifacts(self, exec_dir: Path) -> list[str]:
        """Write assignment artifacts into exec_dir; return pytest filenames."""
        if self.preloaded_artifacts is not None:
            for filename, content in self.preloaded_artifacts.files.items():
                (exec_dir / filename).write_bytes(content)
            return list(self.preloaded_artifacts.pytest_filenames)

        test_filenames: list[str] = []
        for artifact_key, storage_ref in self.artifact_refs.items():
            artifact_config = self.config.artifacts.get(artifact_key)
            if artifact_config is None or artifact_config.type == "model_solution":
                continue

            try:
                content = load_artifact_content(storage_ref)
            except (FileNotFoundError, ValueError) as exc:
                logger.warning("Could not load artifact %s: %s", artifact_key, exc)
                continue

            filename = Path(artifact_config.display_filename or artifact_key).name
            (exec_dir / filename).write_bytes(content)
            if artifact_config.type == "pytest_file":
                test_filenames.append(filename)

        return test_filenames

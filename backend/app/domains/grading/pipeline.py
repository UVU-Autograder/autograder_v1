"""Unified grading pipeline for single-submission evaluation.

Encapsulates submission extraction, static analysis (bundle structure & AST check),
synthesis (artifact injection & test mapping), sandbox execution (Judge0 pytest),
and normalization (rubric scoring & outcome mapping) within an isolated zero-retention workspace.
"""
from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from app.core.settings import get_settings
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.executor import ExecutionOutcome, execute_pytest_in_judge0
from app.domains.grading.protocols import (
    LanguageStrategy,
    ParsedOutcome,
)
from app.domains.grading.result_parser import PytestRunResult, calculate_scores
from app.domains.grading.runtime import (
    ExecutionParameters,
    PreloadedArtifacts,
    load_fallback_helper,
)
from app.domains.grading.strategies import get_strategy
from app.domains.ingestion.extractor import (
    ExtractionError,
    safe_extract_zip,
)
from app.integrations.artifacts.resolver import load_artifact_content
from app.integrations.ast_checker.validator import ASTCheckResult

logger = logging.getLogger(__name__)


@dataclass
class SubmissionPayload:
    """Input payload for a student evaluation.

    Accepts exactly one source form:
    - ``zip_data``: raw ZIP bytes.
    - ``bundle_dir``: directory Path containing submission files.
    - ``files``: in-memory mapping of relative filenames to file bytes.
    """

    zip_data: bytes | None = None
    bundle_dir: Path | None = None
    files: dict[str, bytes] | None = None
    stdin: str | None = None
    official_run_id: int | None = None

    def validate(self) -> None:
        sources = [self.zip_data is not None, self.bundle_dir is not None, self.files is not None]
        if sum(sources) != 1:
            raise ValueError("Provide exactly one of zip_data, bundle_dir, or files")

    @classmethod
    def from_zip(cls, zip_data: bytes, stdin: str | None = None) -> SubmissionPayload:
        return cls(zip_data=zip_data, stdin=stdin)

    @classmethod
    def from_bundle_dir(
        cls,
        bundle_dir: Path,
        stdin: str | None = None,
        official_run_id: int | None = None,
    ) -> SubmissionPayload:
        return cls(bundle_dir=bundle_dir, stdin=stdin, official_run_id=official_run_id)

    @classmethod
    def from_files(
        cls,
        files: dict[str, bytes],
        stdin: str | None = None,
    ) -> SubmissionPayload:
        return cls(files=files, stdin=stdin)


@dataclass
class EvaluationReport:
    """Structured result of a grading pipeline evaluation."""

    success: bool = False
    score: int = 0
    max_score: int = 0
    test_results: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    failure_category: str | None = None
    failure_message: str | None = None
    compiler_errors: list[str] = field(default_factory=list)
    ast_result: ASTCheckResult | None = None
    pytest_result: PytestRunResult | None = None
    parsed_outcome: ParsedOutcome | None = None

    def to_dict(self, run_id: str | None = None) -> dict[str, Any]:
        """Serialize EvaluationReport into a standardized dictionary for state tracking and Redis."""
        data: dict[str, Any] = {
            "success": self.success,
            "score": self.score,
            "max_score": self.max_score,
            "test_results": self.test_results,
            "warnings": self.warnings,
            "failure_category": self.failure_category,
            "failure_message": self.failure_message,
        }
        if self.compiler_errors:
            data["compiler_errors"] = self.compiler_errors
        if run_id is not None:
            data["run_id"] = run_id
        return data


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


class GradingPipeline:
    """Unified single-submission evaluation pipeline.

    Coordinates four distinct grading stages:
    1. Static Analysis: Submission bundle validation & AST policy inspection.
    2. Synthesis: Test artifact injection & helper script preparation.
    3. Sandbox Execution: Judge0 pytest execution within sandbox limits.
    4. Normalization: Pytest result parsing & score calculation.
    """

    def __init__(
        self,
        config: AssignmentConfigV1,
        artifact_refs: dict[str, str],
        allowed_concepts: list[str],
        preloaded_artifacts: PreloadedArtifacts | None = None,
        execution_parameters: ExecutionParameters | None = None,
        runner_source: str | None = None,
        fallback_helper: bytes | None = None,
        strategy: LanguageStrategy | None = None,
        *,
        executor_fn: Callable[..., Any] | None = None,
        load_artifact_fn: Callable[[str], bytes] | None = None,
        load_fallback_helper_fn: Callable[[], bytes] | None = None,
    ) -> None:
        self.config = config
        self.artifact_refs = artifact_refs
        self.allowed_concepts = allowed_concepts
        self.preloaded_artifacts = preloaded_artifacts
        self.settings = get_settings()
        self.execution_parameters = execution_parameters
        self.runner_source = runner_source
        self.fallback_helper = fallback_helper
        if execution_parameters is not None and (runner_source is None or fallback_helper is None):
            raise ValueError("Frozen execution requires captured runner and helper inputs")

        self.strategy = strategy or get_strategy(getattr(self.config.bundle, "language", "python"))
        self.executor_fn = executor_fn or execute_pytest_in_judge0
        self.load_artifact_fn = load_artifact_fn or load_artifact_content
        self.load_fallback_helper_fn = load_fallback_helper_fn or load_fallback_helper

    def evaluate_sync(self, payload: SubmissionPayload) -> EvaluationReport:
        """Synchronous entrypoint for Celery workers and offline execution."""
        import asyncio
        import concurrent.futures

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, self.evaluate(payload)).result()
        return asyncio.run(self.evaluate(payload))

    async def evaluate(self, payload: SubmissionPayload) -> EvaluationReport:
        """Execute the complete evaluation pipeline for a single submission payload."""
        payload.validate()

        workspace = Path(tempfile.mkdtemp(prefix="ag_grade_"))
        report = EvaluationReport(max_score=self.config.base_points)

        try:
            exec_dir = workspace / "execution"

            # Step 0: Extract payload into isolated workspace
            if not self._extract_payload(payload, exec_dir, report):
                return report

            # Stage 1: Static Analysis (Bundle validation & AST inspection)
            if not self._stage_static_analysis(exec_dir, report):
                return report

            # Stage 2: Synthesis (Artifact & helper injection, test case mapping)
            synthesis_output = self._stage_synthesis(exec_dir, report)
            if synthesis_output is None:
                return report
            test_filenames, test_cases_map = synthesis_output

            # Stage 3: Sandbox Execution (Judge0)
            pytest_result = await self._stage_sandbox_execution(
                exec_dir=exec_dir,
                test_filenames=test_filenames,
                test_cases_map=test_cases_map,
                stdin=payload.stdin,
                report=report,
            )
            if pytest_result is None:
                return report

            # Stage 4: Normalization (Scoring & rubric evaluation)
            self._stage_normalization(pytest_result, report)

        finally:
            shutil.rmtree(workspace, ignore_errors=True)

        return report

    def _extract_payload(
        self,
        payload: SubmissionPayload,
        exec_dir: Path,
        report: EvaluationReport,
    ) -> bool:
        """Extract or copy submission files into exec_dir. Returns True on success."""
        if payload.bundle_dir is not None:
            if payload.official_run_id is not None:
                from app.domains.runs.retention import access

                with access(payload.official_run_id):
                    shutil.copytree(payload.bundle_dir, exec_dir)
            else:
                shutil.copytree(payload.bundle_dir, exec_dir)
            return True

        if payload.files is not None:
            exec_dir.mkdir(parents=True, exist_ok=True)
            for rel_path, content in payload.files.items():
                target = (exec_dir / rel_path).resolve()
                if not target.is_relative_to(exec_dir.resolve()):
                    report.failure_category = "unsafe_path"
                    report.failure_message = f"Path traversal attempt: {rel_path}"
                    return False
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            return True

        assert payload.zip_data is not None
        try:
            safe_extract_zip(payload.zip_data, exec_dir)
            return True
        except ExtractionError as exc:
            report.failure_category = "unsafe_zip"
            report.failure_message = str(exc)
            return False

    def _stage_static_analysis(
        self,
        exec_dir: Path,
        report: EvaluationReport,
    ) -> bool:
        """Stage 1: Validate bundle structure and check AST concept rules.

        Delegates to the configured language strategy.
        Returns True if checks pass, False if execution is blocked.
        """
        outcome = self.strategy.static_analysis(exec_dir, self.config, self.allowed_concepts)
        if outcome.ast_result is not None:
            report.ast_result = outcome.ast_result

        for finding in outcome.warnings:
            report.warnings.append(finding)

        if not outcome.passed:
            report.failure_category = outcome.failure_category
            report.failure_message = outcome.failure_message
            return False

        return True

    def _stage_synthesis(
        self,
        exec_dir: Path,
        report: EvaluationReport,
    ) -> tuple[list[str], dict[str, dict[str, list[str]]]] | None:
        """Stage 2: Inject artifacts and helper scripts, build test cases map.

        Returns (test_filenames, test_cases_map) or None on configuration error.
        """
        test_filenames = self._inject_artifacts(exec_dir)

        if self.strategy.language_name == "python":
            helpers_target = exec_dir / "python_autograder_helpers.py"
            if not helpers_target.exists():
                if self.fallback_helper is not None:
                    helpers_target.write_bytes(self.fallback_helper)
                else:
                    try:
                        helpers_target.write_bytes(self.load_fallback_helper_fn())
                    except FileNotFoundError:
                        pass

            if not test_filenames:
                report.failure_category = "validation_error"
                report.failure_message = "No pytest file artifacts found for this assignment."
                return None

        test_cases_map: dict[str, dict[str, list[str]]] = {}
        for test in self.config.scoring_items:
            if test.inputs is not None and test.outputs is not None:
                test_cases_map[test.key] = {
                    "inputs": test.inputs,
                    "outputs": test.outputs,
                }

        return test_filenames, test_cases_map

    async def _stage_sandbox_execution(
        self,
        exec_dir: Path,
        test_filenames: list[str],
        test_cases_map: dict[str, dict[str, list[str]]],
        stdin: str | None,
        report: EvaluationReport,
    ) -> PytestRunResult | None:
        """Stage 3: Execute tests in Judge0 sandbox environment."""
        parameters = self.execution_parameters or ExecutionParameters(
            language_id=self.settings.judge0_language_id,
            cpu_time_limit=float(self.settings.test_execution_timeout_seconds),
            preinstalled_dependencies=sorted(self.settings.preinstalled_dependency_names),
        )

        outcome: ExecutionOutcome = await self.executor_fn(
            exec_dir,
            test_filenames=test_filenames,
            test_cases=test_cases_map,
            entrypoint_module=Path(self.config.bundle.entrypoint).stem,
            language_id=parameters.language_id,
            cpu_time_limit=parameters.cpu_time_limit,
            wall_time_limit=parameters.wall_time_limit,
            memory_limit=parameters.memory_limit,
            runner_source=self.runner_source,
            dependencies=self.config.dependencies,
            stdin=stdin,
        )

        report.pytest_result = outcome.pytest_result
        if not outcome.success:
            report.failure_category = outcome.failure_category
            report.failure_message = outcome.failure_message
            return None

        return outcome.pytest_result

    def _stage_normalization(
        self,
        pytest_result: PytestRunResult | None,
        report: EvaluationReport,
    ) -> None:
        """Stage 4: Parse test outcomes and calculate rubric points."""
        if pytest_result is not None:
            score, test_details = calculate_scores(pytest_result, self.config.scoring_items)
            report.score = score
            report.test_results = test_details
            report.success = True
        elif report.parsed_outcome is not None:
            report.score = report.parsed_outcome.score
            report.test_results = report.parsed_outcome.test_results
            report.success = report.parsed_outcome.success
            if report.parsed_outcome.failure_category:
                report.failure_category = report.parsed_outcome.failure_category
                report.failure_message = report.parsed_outcome.failure_message
            if report.parsed_outcome.compiler_errors:
                report.compiler_errors = report.parsed_outcome.compiler_errors

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
                content = self.load_artifact_fn(storage_ref)
            except (FileNotFoundError, ValueError) as exc:
                logger.warning("Could not load artifact %s: %s", artifact_key, exc)
                continue

            filename = Path(artifact_config.display_filename or artifact_key).name
            (exec_dir / filename).write_bytes(content)
            if artifact_config.type == "pytest_file":
                test_filenames.append(filename)

        return test_filenames

"""Concrete grading strategy for Python assignments evaluated via Pytest."""
from __future__ import annotations

import base64
import io
import logging
import zipfile
from pathlib import Path
from typing import Any

from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.protocols import (
    ExecutionCommand,
    ExecutionPayload,
    ExecutionRawResult,
    LanguageStrategy,
    ParsedOutcome,
    StaticAnalysisOutcome,
)
from app.domains.grading.result_parser import (
    PytestRunResult,
    calculate_scores,
    parse_pytest_json,
)
from app.domains.grading.runner_gen import generate_runner_script
from app.domains.ingestion.extractor import validate_submission_bundle
from app.integrations.ast_checker.validator import ASTCodeInspector

logger = logging.getLogger(__name__)


def _build_additional_files_b64(exec_dir: Path) -> str:
    """ZIP *exec_dir* for Judge0 additional_files (excludes runner.py)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in exec_dir.rglob("*"):
            if item.is_file() and item.name != "runner.py":
                zf.write(item, str(item.relative_to(exec_dir)))
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class PythonPytestStrategy(LanguageStrategy):
    """Executes and scores Python coursework using Pytest inside Judge0."""

    @property
    def language_name(self) -> str:
        return "python"

    def static_analysis(
        self,
        exec_dir: Path,
        config: AssignmentConfigV1,
        allowed_concepts: list[str],
    ) -> StaticAnalysisOutcome:
        """Validate Python bundle files and verify AST concept boundaries."""
        try:
            validate_submission_bundle(exec_dir, config)
        except ValueError as exc:
            category = "missing_required_file"
            msg = str(exc)
            if "entrypoint" in msg.lower():
                category = "ambiguous_entrypoint"
            return StaticAnalysisOutcome(
                passed=False,
                failure_category=category,
                failure_message=msg,
            )

        inspector = ASTCodeInspector(allowed_concepts=allowed_concepts)
        ast_result = inspector.inspect_directory(exec_dir)

        warnings: list[dict[str, Any]] = [
            {"code": finding.code, "message": finding.message}
            for finding in ast_result.warnings
        ]

        if ast_result.is_blocked:
            blocked_msgs = [f.message for f in ast_result.blocked]
            return StaticAnalysisOutcome(
                passed=False,
                warnings=warnings,
                failure_category="concept_blocked",
                failure_message="; ".join(blocked_msgs),
                ast_result=ast_result,
            )

        return StaticAnalysisOutcome(
            passed=True,
            warnings=warnings,
            ast_result=ast_result,
        )

    def prepare_bundle(
        self,
        exec_dir: Path,
        config: AssignmentConfigV1,
        support_artifacts: dict[str, bytes],
        stdin: str | None = None,
        *,
        language_id: int | None = None,
        cpu_time_limit: float | None = None,
        memory_limit: int | None = None,
        wall_time_limit: float | None = None,
        runner_source: str | None = None,
    ) -> ExecutionPayload:
        """Assemble Python execution runner and package additional files."""
        # Find test files in directory
        test_filenames = [
            f.name
            for f in exec_dir.iterdir()
            if f.is_file() and (f.name.startswith("test_") or f.name.endswith("_test.py") or f.name == "tests.py")
        ]

        test_cases_map: dict[str, dict[str, list[str]]] = {}
        for test in config.scoring_items:
            if test.inputs is not None and test.outputs is not None:
                test_cases_map[test.key] = {
                    "inputs": test.inputs,
                    "outputs": test.outputs,
                }

        entrypoint_module = Path(config.bundle.entrypoint).stem

        runner_code = runner_source or generate_runner_script(
            test_filenames,
            test_cases_map,
            entrypoint_module,
            config.dependencies,
        )

        additional_files = _build_additional_files_b64(exec_dir)

        return ExecutionPayload(
            source_code=runner_code,
            language_id=language_id or 711,
            additional_files_b64=additional_files,
            compile_cmd=self.compile_command(),
            test_cmd=self.test_command(),
            cpu_time_limit=cpu_time_limit or 30.0,
            wall_time_limit=wall_time_limit or 60.0,
            memory_limit=memory_limit or 512000,
            stdin=stdin,
        )

    def compile_command(self) -> ExecutionCommand | None:
        """Python is an interpreted language; no compilation step required."""
        return None

    def test_command(self) -> ExecutionCommand:
        """Pytest test command."""
        return ExecutionCommand(
            command="python3",
            args=["runner.py"],
            timeout_seconds=30.0,
        )

    def parse_execution(
        self,
        raw_result: ExecutionRawResult,
        config: AssignmentConfigV1,
    ) -> ParsedOutcome:
        """Parse pytest JSON stdout and compute rubric scores."""
        pytest_result: PytestRunResult = parse_pytest_json(raw_result.stdout)
        score, test_details = calculate_scores(pytest_result, config.scoring_items)

        is_success = (
            raw_result.exit_code == 0
            or (raw_result.exit_code in (0, 1) and pytest_result.total > 0 and pytest_result.error_message is None)
        )

        failure_category: str | None = None
        failure_message: str | None = None
        if not is_success and pytest_result.error_message:
            failure_category = "test_execution_error"
            failure_message = pytest_result.error_message

        return ParsedOutcome(
            success=is_success,
            score=score,
            max_score=config.base_points,
            test_results=test_details,
            failure_category=failure_category,
            failure_message=failure_message,
            raw_data=pytest_result,
        )

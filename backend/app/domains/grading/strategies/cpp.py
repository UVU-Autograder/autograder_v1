"""Concrete grading strategy for C/C++ coursework with compiler diagnostics and test parsing."""
from __future__ import annotations

import base64
import io
import logging
import re
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

logger = logging.getLogger(__name__)

COMPILER_ERROR_RE = re.compile(r"^(.*?):(\d+):(?:\d+:)?\s*(fatal error|error):\s*(.*)$", re.MULTILINE)
GTEST_PASSED_RE = re.compile(r"\[\s*PASSED\s*\]\s*(\w+)\.(\w+)")
GTEST_FAILED_RE = re.compile(r"\[\s*FAILED\s*\]\s*(\w+)\.(\w+)")


def _build_additional_files_b64(exec_dir: Path) -> str:
    """ZIP *exec_dir* for Judge0 additional_files."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in exec_dir.rglob("*"):
            if item.is_file() and item.name != "runner.sh":
                zf.write(item, str(item.relative_to(exec_dir)))
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class CppStrategy(LanguageStrategy):
    """Executes and scores C/C++ coursework with GCC/Clang compilation diagnostics."""

    @property
    def language_name(self) -> str:
        return "cpp"

    def static_analysis(
        self,
        exec_dir: Path,
        config: AssignmentConfigV1,
        allowed_concepts: list[str],
    ) -> StaticAnalysisOutcome:
        """Validate C/C++ file presence and header completeness."""
        # Verify entrypoint file exists
        entrypoint_file = exec_dir / config.bundle.entrypoint
        if not entrypoint_file.is_file():
            return StaticAnalysisOutcome(
                passed=False,
                failure_category="missing_required_file",
                failure_message=f"Required entrypoint file '{config.bundle.entrypoint}' is missing.",
            )

        # Check required files
        for req in config.bundle.file_requirements:
            if req.paths:
                for path_str in req.paths:
                    if not (exec_dir / path_str).is_file():
                        return StaticAnalysisOutcome(
                            passed=False,
                            failure_category="missing_required_file",
                            failure_message=f"Required file '{path_str}' ({req.label}) is missing.",
                        )

        return StaticAnalysisOutcome(passed=True)

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
        """Prepare C/C++ compilation script and package files."""
        # Language ID 54 = C++ (GCC 9.2.0) or 75 = C++ (Clang 10.0.1) in Judge0
        cpp_lang_id = language_id or 54

        # Script that compiles student solution with GoogleTest and executes runner
        compile_script = runner_source or (
            "#!/usr/bin/env bash\n"
            "set -e\n"
            "g++ -std=c++17 -Wall -Wextra -O2 *.cpp -lgtest -lgtest_main -pthread -o test_runner\n"
            "./test_runner\n"
        )

        additional_files = _build_additional_files_b64(exec_dir)

        return ExecutionPayload(
            source_code=compile_script,
            language_id=cpp_lang_id,
            additional_files_b64=additional_files,
            compile_cmd=self.compile_command(),
            test_cmd=self.test_command(),
            cpu_time_limit=cpu_time_limit or 30.0,
            wall_time_limit=wall_time_limit or 60.0,
            memory_limit=memory_limit or 512000,
            stdin=stdin,
        )

    def compile_command(self) -> ExecutionCommand:
        """GCC C++17 compilation command."""
        return ExecutionCommand(
            command="g++",
            args=["-std=c++17", "-Wall", "-Wextra", "-O2", "*.cpp", "-o", "test_runner"],
            timeout_seconds=30.0,
        )

    def test_command(self) -> ExecutionCommand:
        """Binary execution command."""
        return ExecutionCommand(
            command="./test_runner",
            args=[],
            timeout_seconds=30.0,
        )

    def parse_execution(
        self,
        raw_result: ExecutionRawResult,
        config: AssignmentConfigV1,
    ) -> ParsedOutcome:
        """Extract compiler diagnostics and GoogleTest pass/fail markers."""
        output = f"{raw_result.stdout}\n{raw_result.stderr}\n{raw_result.compile_output or ''}"

        # 1. Check for compiler diagnostics
        compiler_errors: list[str] = []
        for match in COMPILER_ERROR_RE.finditer(output):
            filename, line_num, severity, message = match.groups()
            compiler_errors.append(f"{filename}:{line_num}: {severity}: {message.strip()}")

        if compiler_errors:
            return ParsedOutcome(
                success=False,
                score=0,
                max_score=config.base_points,
                failure_category="compilation_error",
                failure_message=f"Build failed with {len(compiler_errors)} compiler error(s).",
                compiler_errors=compiler_errors,
            )

        # 2. Parse GoogleTest output
        passed_tests = {f"{suite}.{test}" for suite, test in GTEST_PASSED_RE.findall(output)}
        failed_tests = {f"{suite}.{test}" for suite, test in GTEST_FAILED_RE.findall(output)}

        test_results: list[dict[str, Any]] = []
        total_score = 0

        for item in config.scoring_items:
            # Check match by key or case
            matched_pass = any(item.key.lower() in t.lower() for t in passed_tests)
            matched_fail = any(item.key.lower() in t.lower() for t in failed_tests)
            passed = matched_pass and not matched_fail

            if passed:
                points_awarded = item.points
                status = "passed"
                total_score += points_awarded
            else:
                points_awarded = 0
                status = "failed"

            test_results.append({
                "key": item.key,
                "label": item.label,
                "status": status,
                "passed": passed,
                "points": item.points,
                "points_awarded": points_awarded,
                "points_possible": item.points,
            })

        is_success = raw_result.exit_code == 0 or len(passed_tests) > 0 or len(failed_tests) > 0

        return ParsedOutcome(
            success=is_success,
            score=total_score,
            max_score=config.base_points,
            test_results=test_results,
            failure_category=None if is_success else "test_execution_error",
            failure_message=None if is_success else "One or more tests failed execution.",
        )

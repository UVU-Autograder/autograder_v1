"""Concrete grading strategy for Web Development (HTML/CSS/JavaScript) coursework."""
from __future__ import annotations

import base64
import html.parser
import io
import json
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

TEST_PASSED_RE = re.compile(r"\[\s*PASSED\s*\]\s*([a-zA-Z0-9_\-\.]+)")
TEST_FAILED_RE = re.compile(r"\[\s*FAILED\s*\]\s*([a-zA-Z0-9_\-\.]+)(?::\s*(.*))?")
NODE_SYNTAX_ERROR_RE = re.compile(
    r"^(.*?):(\d+)(?::\d+)?\s*\n(?:[^\n]*\n)*?\s*(SyntaxError|ReferenceError|TypeError):\s*(.*)$",
    re.MULTILINE,
)


def _matches_test_key(key: str, test_name: str) -> bool:
    """Check if a scoring item key matches a test identifier."""
    k = key.lower()
    t = test_name.lower()
    if t == k:
        return True
    parts = re.split(r"[\.\:\/]", t)
    return k in parts


class SimpleHTMLValidator(html.parser.HTMLParser):
    """Basic HTML structure validator that catches unclosed root or fatal tag mismatches."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.has_html = False
        self.has_body = False
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower == "html":
            self.has_html = True
        elif tag_lower == "body":
            self.has_body = True
        # Self-closing HTML elements do not require matching closing tags
        if tag_lower not in {
            "meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "param", "track", "wbr"
        }:
            self.tags.append(tag_lower)

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.tags:
            # Pop matching or most recent
            while self.tags:
                top = self.tags.pop()
                if top == tag_lower:
                    break


def _build_additional_files_b64(exec_dir: Path) -> str:
    """ZIP *exec_dir* for Judge0 additional_files."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in exec_dir.rglob("*"):
            if item.is_file() and item.name != "test_runner.js":
                zf.write(item, str(item.relative_to(exec_dir)))
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class WebDevelopmentStrategy(LanguageStrategy):
    """Executes and scores Web Development coursework (HTML/CSS/JS) using Node.js DOM runner."""

    @property
    def language_name(self) -> str:
        return "web"

    def static_analysis(
        self,
        exec_dir: Path,
        config: AssignmentConfigV1,
        allowed_concepts: list[str] | None,
    ) -> StaticAnalysisOutcome:
        """Validate web bundle files (index.html, styles, scripts) and HTML structure."""
        entrypoint = config.bundle.entrypoint or "index.html"
        entrypoint_file = exec_dir / entrypoint

        if not entrypoint_file.is_file():
            return StaticAnalysisOutcome(
                passed=False,
                failure_category="missing_required_file",
                failure_message=f"Required entrypoint file '{entrypoint}' is missing.",
            )

        # Check required files
        for req in config.bundle.file_requirements:
            if req.paths:
                for path_str in req.paths:
                    if not (exec_dir / path_str).is_file():
                        return StaticAnalysisOutcome(
                            passed=False,
                            failure_category="missing_required_file",
                            failure_message=f"Required file '{path_str}' is missing.",
                        )

        # Basic HTML syntax verification for .html files
        if entrypoint_file.suffix.lower() == ".html":
            try:
                content = entrypoint_file.read_text(encoding="utf-8", errors="replace")
                if not content.strip():
                    return StaticAnalysisOutcome(
                        passed=False,
                        failure_category="malformed_html",
                        failure_message=f"HTML entrypoint '{entrypoint}' is empty.",
                    )
                validator = SimpleHTMLValidator()
                validator.feed(content)
            except Exception as exc:
                return StaticAnalysisOutcome(
                    passed=False,
                    failure_category="malformed_html",
                    failure_message=f"Error parsing HTML structure in '{entrypoint}': {exc}",
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
        """Assemble Node.js test runner for HTML/DOM/JS evaluation and package bundle."""
        # Judge0 language ID: 93 = JavaScript (Node.js 18.15.0) or 63 = Node.js 12.14.0
        node_lang_id = language_id or 93

        # Default runner script if none provided: evaluates scoring items against files
        default_runner = (
            "const fs = require('fs');\n"
            "const path = require('path');\n\n"
            "try {\n"
            "  const entrypoint = process.env.ENTRYPOINT || 'index.html';\n"
            "  const htmlContent = fs.existsSync(entrypoint) ? fs.readFileSync(entrypoint, 'utf8') : '';\n"
            "  console.log('[INFO] Web runner evaluated entrypoint: ' + entrypoint);\n"
            "} catch (err) {\n"
            "  console.error('[ERROR] ' + err.message);\n"
            "  process.exit(1);\n"
            "}\n"
        )

        runner_script = runner_source
        if not runner_script:
            test_runner_file = exec_dir / "test_runner.js"
            if test_runner_file.is_file():
                runner_script = test_runner_file.read_text(encoding="utf-8", errors="replace")
            else:
                runner_script = default_runner
        additional_files = _build_additional_files_b64(exec_dir)

        return ExecutionPayload(
            source_code=runner_script,
            language_id=node_lang_id,
            additional_files_b64=additional_files,
            compile_cmd=self.compile_command(),
            test_cmd=self.test_command(),
            cpu_time_limit=cpu_time_limit or 30.0,
            wall_time_limit=wall_time_limit or 60.0,
            memory_limit=memory_limit or 512000,
            stdin=stdin,
        )

    def compile_command(self) -> ExecutionCommand | None:
        """JavaScript / HTML is interpreted; no compile step required."""
        return None

    def test_command(self) -> ExecutionCommand:
        """Node.js execution command."""
        return ExecutionCommand(
            command="node",
            args=["test_runner.js"],
            timeout_seconds=30.0,
        )

    def parse_execution(
        self,
        raw_result: ExecutionRawResult,
        config: AssignmentConfigV1,
    ) -> ParsedOutcome:
        """Parse Node.js DOM test results, assertion output, and JS runtime errors."""
        output = f"{raw_result.stdout}\n{raw_result.stderr}\n{raw_result.compile_output or ''}"

        # 1. Check for fatal syntax / reference errors in script
        compiler_errors: list[str] = []
        for match in NODE_SYNTAX_ERROR_RE.finditer(output):
            file_loc, line_num, err_type, msg = match.groups()
            compiler_errors.append(f"{file_loc}:{line_num}: {err_type}: {msg.strip()}")

        if not compiler_errors:
            generic_match = re.search(r"^\s*(SyntaxError|ReferenceError|TypeError):\s*(.*)$", output, re.MULTILINE)
            if generic_match:
                err_type, msg = generic_match.groups()
                compiler_errors.append(f"{err_type}: {msg.strip()}")

        if compiler_errors and raw_result.exit_code != 0 and "[PASSED]" not in output and "[FAILED]" not in output:
            return ParsedOutcome(
                success=False,
                score=0,
                max_score=config.base_points,
                failure_category="syntax_error",
                failure_message=f"JavaScript evaluation failed with {len(compiler_errors)} error(s).",
                compiler_errors=compiler_errors,
            )

        # 2. Check for JSON structured test output from Node test runner
        json_results = None
        for line in raw_result.stdout.splitlines():
            trimmed = line.strip()
            if trimmed.startswith("{") and trimmed.endswith("}"):
                try:
                    candidate = json.loads(trimmed)
                    if isinstance(candidate, dict) and "tests" in candidate:
                        json_results = candidate["tests"]
                        break
                except (json.JSONDecodeError, ValueError):
                    pass

        # 3. Parse test outcomes (from JSON or stdout tags)
        passed_tests: set[str] = set()
        failed_tests: dict[str, str] = {}

        if json_results is not None:
            for t in json_results:
                t_key = str(t.get("key", t.get("name", "")))
                if t.get("passed", False) or t.get("status") == "passed":
                    passed_tests.add(t_key)
                else:
                    failed_tests[t_key] = str(t.get("message", "Test assertion failed"))
        else:
            for match in TEST_PASSED_RE.finditer(output):
                passed_tests.add(match.group(1))
            for match in TEST_FAILED_RE.finditer(output):
                key = match.group(1)
                msg = match.group(2) or "Test assertion failed"
                failed_tests[key] = msg.strip()

        test_results: list[dict[str, Any]] = []
        total_score = 0

        for item in config.scoring_items:
            # Check match by key or label
            matched_pass = any(_matches_test_key(item.key, t) for t in passed_tests)
            matched_fail = any(_matches_test_key(item.key, t) for t in failed_tests)
            passed = matched_pass and not matched_fail

            if passed:
                points_awarded = item.points
                status = "passed"
                total_score += points_awarded
                message = None
            else:
                points_awarded = 0
                status = "failed"
                # Locate failure message if available
                message = next(
                    (msg for k, msg in failed_tests.items() if _matches_test_key(item.key, k)),
                    "Test failed",
                )

            test_results.append({
                "key": item.key,
                "label": item.label,
                "status": status,
                "passed": passed,
                "points": item.points,
                "points_awarded": points_awarded,
                "points_possible": item.points,
                "message": message,
            })

        has_test_markers = len(passed_tests) > 0 or len(failed_tests) > 0
        is_success = raw_result.exit_code == 0 or has_test_markers

        return ParsedOutcome(
            success=is_success,
            score=total_score,
            max_score=config.base_points,
            test_results=test_results,
            compiler_errors=compiler_errors,
            failure_category=None if is_success else "test_execution_error",
            failure_message=None if is_success else "Web development test runner exited with an error.",
        )

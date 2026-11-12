"""Tests for WebDevelopmentStrategy (HTML/CSS/JS coursework)."""
from __future__ import annotations

import json
from pathlib import Path

from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.protocols import (
    ExecutionPayload,
    ExecutionRawResult,
    LanguageRunner,
    LanguageStrategy,
    OutcomeParser,
)
from app.domains.grading.strategies import (
    WebDevelopmentStrategy,
    get_strategy,
)


def test_web_strategy_protocol_adherence() -> None:
    """Verify WebDevelopmentStrategy satisfies language protocols."""
    strat = WebDevelopmentStrategy()
    assert isinstance(strat, LanguageRunner)
    assert isinstance(strat, OutcomeParser)
    assert isinstance(strat, LanguageStrategy)
    assert strat.language_name == "web"


def test_registry_resolves_web_and_aliases() -> None:
    """Verify registry resolves 'web', 'javascript', and 'html'."""
    assert isinstance(get_strategy("web"), WebDevelopmentStrategy)
    assert isinstance(get_strategy("WEB"), WebDevelopmentStrategy)
    assert isinstance(get_strategy("javascript"), WebDevelopmentStrategy)
    assert isinstance(get_strategy("html"), WebDevelopmentStrategy)


def test_web_strategy_static_analysis_missing_entrypoint(tmp_path: Path) -> None:
    """Missing entrypoint triggers static analysis failure."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [{"key": "dom_h1", "label": "Heading", "points": 10, "extra_credit": False}],
    })

    outcome = strat.static_analysis(tmp_path, config, allowed_concepts=[])
    assert not outcome.passed
    assert outcome.failure_category == "missing_required_file"
    assert "index.html" in (outcome.failure_message or "")


def test_web_strategy_static_analysis_missing_required_file(tmp_path: Path) -> None:
    """Missing secondary required file (e.g. styles.css) triggers failure."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [
                {"paths": ["index.html"]},
                {"paths": ["styles.css"]},
            ],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [{"key": "dom_h1", "label": "Heading", "points": 10, "extra_credit": False}],
    })

    (tmp_path / "index.html").write_text("<!DOCTYPE html><html><body><h1>Title</h1></body></html>", encoding="utf-8")
    outcome = strat.static_analysis(tmp_path, config, allowed_concepts=[])
    assert not outcome.passed
    assert outcome.failure_category == "missing_required_file"
    assert "styles.css" in (outcome.failure_message or "")


def test_web_strategy_static_analysis_empty_html(tmp_path: Path) -> None:
    """Empty HTML entrypoint triggers malformed_html failure."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [{"key": "dom_h1", "label": "Heading", "points": 10, "extra_credit": False}],
    })

    (tmp_path / "index.html").write_text("   \n  ", encoding="utf-8")
    outcome = strat.static_analysis(tmp_path, config, allowed_concepts=[])
    assert not outcome.passed
    assert outcome.failure_category == "malformed_html"


def test_web_strategy_static_analysis_success(tmp_path: Path) -> None:
    """Valid files pass static analysis."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [
                {"paths": ["index.html"]},
                {"paths": ["styles.css"]},
                {"paths": ["script.js"]},
            ],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [{"key": "dom_h1", "label": "Heading", "points": 10, "extra_credit": False}],
    })

    (tmp_path / "index.html").write_text("<!DOCTYPE html><html><head><link rel='stylesheet' href='styles.css'></head><body><h1>Hello</h1><script src='script.js'></script></body></html>", encoding="utf-8")
    (tmp_path / "styles.css").write_text("h1 { color: red; }", encoding="utf-8")
    (tmp_path / "script.js").write_text("console.log('ready');", encoding="utf-8")

    outcome = strat.static_analysis(tmp_path, config, allowed_concepts=[])
    assert outcome.passed


def test_web_strategy_prepare_bundle(tmp_path: Path) -> None:
    """Verify bundle packaging for Node.js execution."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [{"key": "dom_check", "label": "DOM Check", "points": 20, "extra_credit": False}],
    })

    (tmp_path / "index.html").write_text("<h1>Test</h1>", encoding="utf-8")
    payload = strat.prepare_bundle(
        exec_dir=tmp_path,
        config=config,
        support_artifacts={},
    )

    assert isinstance(payload, ExecutionPayload)
    assert payload.language_id == 93
    assert len(payload.additional_files_b64) > 0
    assert strat.compile_command() is None
    assert strat.test_command().command == "node"


def test_web_strategy_parse_syntax_error() -> None:
    """Verify JavaScript syntax errors in execution output are captured."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [{"key": "calc_tax", "label": "Tax Calculation", "points": 50, "extra_credit": False}],
    })

    stderr = "script.js:14\nSyntaxError: Unexpected token '}'\n    at wrapSafe (node:internal/modules/cjs/loader:1280:20)"
    raw = ExecutionRawResult(stdout="", stderr=stderr, exit_code=1)

    parsed = strat.parse_execution(raw, config)
    assert not parsed.success
    assert parsed.score == 0
    assert parsed.failure_category == "syntax_error"
    assert len(parsed.compiler_errors) >= 1
    assert "SyntaxError: Unexpected token" in parsed.compiler_errors[0]


def test_web_strategy_parse_json_test_results() -> None:
    """Verify JSON-formatted DOM test results are parsed into scoring items."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [
            {"key": "test_header", "label": "Header element", "points": 30, "extra_credit": False},
            {"key": "test_button_click", "label": "Button click event", "points": 70, "extra_credit": False},
        ],
    })

    json_report = json.dumps({
        "tests": [
            {"key": "test_header", "status": "passed", "passed": True},
            {"key": "test_button_click", "status": "failed", "passed": False, "message": "Expected count 1 but got 0"},
        ]
    })
    stdout = f"Running web tests...\n{json_report}\nCompleted in 45ms"
    raw = ExecutionRawResult(stdout=stdout, exit_code=1)

    parsed = strat.parse_execution(raw, config)
    assert parsed.success
    assert parsed.score == 30
    assert len(parsed.test_results) == 2
    assert parsed.test_results[0]["passed"] is True
    assert parsed.test_results[0]["points_awarded"] == 30
    assert parsed.test_results[1]["passed"] is False
    assert parsed.test_results[1]["points_awarded"] == 0
    assert "Expected count 1" in parsed.test_results[1]["message"]


def test_web_strategy_parse_stdout_markers() -> None:
    """Verify standard [PASSED] / [FAILED] markers are parsed into scoring items."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [
            {"key": "dom_nav", "label": "Navigation bar", "points": 40, "extra_credit": False},
            {"key": "dom_footer", "label": "Footer copyright", "points": 60, "extra_credit": False},
        ],
    })

    stdout = (
        "[PASSED] dom_nav\n"
        "[FAILED] dom_footer: Missing &copy; symbol in footer element\n"
    )
    raw = ExecutionRawResult(stdout=stdout, exit_code=1)

    parsed = strat.parse_execution(raw, config)
    assert parsed.success
    assert parsed.score == 40
    assert parsed.test_results[0]["status"] == "passed"
    assert parsed.test_results[0]["points_awarded"] == 40
    assert parsed.test_results[1]["status"] == "failed"
    assert parsed.test_results[1]["points_awarded"] == 0
    assert "Missing &copy;" in parsed.test_results[1]["message"]


def test_web_strategy_parse_real_node_syntax_error_with_caret() -> None:
    """Verify realistic multi-line Node.js syntax errors with source line and caret are captured."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [{"key": "calc_tax", "label": "Tax Calculation", "points": 50, "extra_credit": False}],
    })

    stderr = (
        "/workspace/script.js:5\n"
        "const x = ;\n"
        "          ^\n\n"
        "SyntaxError: Unexpected token ';'\n"
        "    at wrapSafe (node:internal/modules/cjs/loader:1280:20)\n"
    )
    raw = ExecutionRawResult(stdout="", stderr=stderr, exit_code=1)

    parsed = strat.parse_execution(raw, config)
    assert not parsed.success
    assert parsed.score == 0
    assert parsed.failure_category == "syntax_error"
    assert len(parsed.compiler_errors) >= 1
    assert "script.js:5" in parsed.compiler_errors[0]
    assert "Unexpected token" in parsed.compiler_errors[0]


def test_web_strategy_test_key_collision_avoidance() -> None:
    """Verify test_1 does not pass just because test_10 passed (no substring false positives)."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [
            {"key": "test_1", "label": "Test 1", "points": 25, "extra_credit": False},
            {"key": "test_10", "label": "Test 10", "points": 25, "extra_credit": False},
        ],
    })

    stdout = (
        "[FAILED] test_1: Assertion failed\n"
        "[PASSED] test_10\n"
    )
    raw = ExecutionRawResult(stdout=stdout, exit_code=1)

    parsed = strat.parse_execution(raw, config)
    assert parsed.score == 25
    assert parsed.test_results[0]["passed"] is False
    assert parsed.test_results[0]["points_awarded"] == 0
    assert parsed.test_results[1]["passed"] is True
    assert parsed.test_results[1]["points_awarded"] == 25


def test_web_strategy_resolves_test_runner_from_exec_dir(tmp_path: Path) -> None:
    """Verify prepare_bundle uses test_runner.js present in exec_dir when runner_source is None."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"test_harness": {"type": "support_file", "display_filename": "test_runner.js"}},
        "scoring_items": [{"key": "dom_h1", "label": "Heading", "points": 10, "extra_credit": False}],
    })

    (tmp_path / "index.html").write_text("<h1>Hello</h1>", encoding="utf-8")
    (tmp_path / "test_runner.js").write_text("// CUSTOM HARNESS CODE", encoding="utf-8")

    payload = strat.prepare_bundle(tmp_path, config, support_artifacts={})
    assert payload.source_code == "// CUSTOM HARNESS CODE"

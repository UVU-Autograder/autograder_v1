"""Tests for WebDevelopmentStrategy (HTML/CSS/JS coursework)."""
from __future__ import annotations

import base64
import io
import json
import zipfile
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
from test_multilang_integration import protocol2_report


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


def test_web_strategy_static_analysis_rejects_reserved_harness_files(tmp_path: Path) -> None:
    """Submissions cannot ship files that collide with the trusted multi-file harness."""
    strat = WebDevelopmentStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": {"type": "test_file", "display_filename": "tests.cjs"}},
        "scoring_items": [{"key": "dom_h1", "label": "Heading", "points": 10, "extra_credit": False}],
    })

    (tmp_path / "index.html").write_text("<h1>Title</h1>", encoding="utf-8")
    (tmp_path / "ag_web_runner.cjs").write_text("process.exit(0)", encoding="utf-8")
    outcome = strat.static_analysis(tmp_path, config, allowed_concepts=[])
    assert not outcome.passed
    assert outcome.failure_category == "missing_required_file"
    assert "ag_web_runner.cjs" in (outcome.failure_message or "") or "Reserved" in (outcome.failure_message or "")


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


def _web_config(*items: tuple[str, str, int], artifact: dict | None = None) -> AssignmentConfigV1:
    return AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {"tests": artifact or {"type": "test_file", "display_filename": "tests.cjs"}},
        "scoring_items": [{"key": key, "label": label, "points": points, "extra_credit": False}
                          for key, label, points in items],
    })


def test_web_strategy_prepare_bundle(tmp_path: Path) -> None:
    """Verify bundle packaging for the trusted jsdom adapter on Judge0 language 89."""
    strat = WebDevelopmentStrategy()
    config = _web_config(("dom_check", "DOM Check", 20))
    assert config.test_framework == "jsdom"

    (tmp_path / "index.html").write_text("<h1>Test</h1>", encoding="utf-8")
    (tmp_path / "tests.cjs").write_text("module.exports = () => {};", encoding="utf-8")
    payload = strat.prepare_bundle(
        exec_dir=tmp_path,
        config=config,
        support_artifacts={},
    )

    assert isinstance(payload, ExecutionPayload)
    assert payload.language_id == 89
    assert payload.source_code is None
    assert len(payload.additional_files_b64) > 0
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload.additional_files_b64))) as archive:
        names = set(archive.namelist())
        assert {"index.html", "tests.cjs", "run", "ag_adapter.py", "ag_config.json"} <= names
        assert "compile" not in names  # interpreted: nothing to build
        assert json.loads(archive.read("ag_config.json"))["test_files"] == ["tests.cjs"]
    assert strat.compile_command() is None
    assert strat.test_command().command == "run"


def test_web_strategy_runner_error_is_reported_through_the_envelope() -> None:
    """A script/runner failure arrives as an infrastructure_error report, not scraped stderr text."""
    strat = WebDevelopmentStrategy()
    config = _web_config(("calc_tax", "Tax Calculation", 50))

    report = protocol2_report([], completed=False, exit_code=3,
                              infrastructure_error="RuntimeError: Web runner did not complete.")
    stderr = "script.js:14\nSyntaxError: Unexpected token '}'\n    at wrapSafe (node:internal/modules/cjs/loader:1280:20)"
    parsed = strat.parse_execution(ExecutionRawResult(stdout=report, stderr=stderr, exit_code=0), config)

    assert not parsed.success
    assert parsed.score == 0
    assert parsed.failure_category == "infrastructure_error"
    assert "Web runner did not complete" in (parsed.failure_message or "")


def test_web_strategy_stderr_without_a_report_is_never_scraped() -> None:
    """Node-style syntax errors on stderr (with or without a caret) do not become scored/categorized output."""
    strat = WebDevelopmentStrategy()
    config = _web_config(("calc_tax", "Tax Calculation", 50))

    stderr = (
        "/workspace/script.js:5\n"
        "const x = ;\n"
        "          ^\n\n"
        "SyntaxError: Unexpected token ';'\n"
        "    at wrapSafe (node:internal/modules/cjs/loader:1280:20)\n"
    )
    parsed = strat.parse_execution(ExecutionRawResult(stdout="", stderr=stderr, exit_code=1, status_id=11), config)

    assert not parsed.success
    assert parsed.score == 0
    assert parsed.failure_category == "invalid_runner_report"
    assert parsed.compiler_errors == []


def test_web_strategy_parse_protocol2_test_results() -> None:
    """Verify protocol-2 DOM test results are mapped to scoring items by rubric marker."""
    strat = WebDevelopmentStrategy()
    config = _web_config(("test_header", "Header element", 30), ("test_button_click", "Button click event", 70))

    report = protocol2_report([
        {"nodeid": "tests.cjs::header", "key": "test_header"},
        {"nodeid": "tests.cjs::click", "key": "test_button_click", "outcome": "failed",
         "message": "Expected count 1 but got 0"},
    ])
    raw = ExecutionRawResult(stdout=report, exit_code=1, status_id=11)

    parsed = strat.parse_execution(raw, config)
    assert parsed.success
    assert parsed.score == 30
    assert len(parsed.test_results) == 2
    assert parsed.test_results[0]["passed"] is True
    assert parsed.test_results[0]["points_awarded"] == 30
    assert parsed.test_results[1]["passed"] is False
    assert parsed.test_results[1]["points_awarded"] == 0
    assert "Expected count 1" in parsed.test_results[1]["test_results"][0]["message"]


def test_web_strategy_ignores_console_markers_and_json_lookalikes() -> None:
    """Console [PASSED]/[FAILED] banners and ad hoc JSON lines never score."""
    strat = WebDevelopmentStrategy()
    config = _web_config(("dom_nav", "Navigation bar", 40), ("dom_footer", "Footer copyright", 60))

    for stdout in (
        "[PASSED] dom_nav\n[FAILED] dom_footer: Missing &copy; symbol in footer element\n",
        'Running web tests...\n{"tests": [{"key": "dom_nav", "status": "passed", "passed": true}]}\nDone',
    ):
        parsed = strat.parse_execution(ExecutionRawResult(stdout=stdout, exit_code=0), config)
        assert not parsed.success
        assert parsed.score == 0
        assert parsed.test_results == []
        assert parsed.failure_category == "invalid_runner_report"


def test_web_strategy_test_key_collision_avoidance() -> None:
    """Verify test_1 does not pass just because test_10 passed (no substring false positives)."""
    strat = WebDevelopmentStrategy()
    config = _web_config(("test_1", "Test 1", 25), ("test_10", "Test 10", 25))

    report = protocol2_report([
        {"nodeid": "tests.cjs::one", "key": "test_1", "outcome": "failed", "message": "Assertion failed"},
        {"nodeid": "tests.cjs::ten", "key": "test_10"},
    ])
    raw = ExecutionRawResult(stdout=report, exit_code=1, status_id=11)

    parsed = strat.parse_execution(raw, config)
    assert parsed.score == 25
    assert parsed.test_results[0]["passed"] is False
    assert parsed.test_results[0]["points_awarded"] == 0
    assert parsed.test_results[1]["passed"] is True
    assert parsed.test_results[1]["points_awarded"] == 25


def test_web_strategy_never_promotes_exec_dir_files_to_source_code(tmp_path: Path) -> None:
    """A file named like a runner in exec_dir is just data; Judge0 receives no source_code at all."""
    strat = WebDevelopmentStrategy()
    config = _web_config(("dom_h1", "Heading", 10),
                         artifact={"type": "test_file", "display_filename": "test_runner.js"})

    (tmp_path / "index.html").write_text("<h1>Hello</h1>", encoding="utf-8")
    (tmp_path / "test_runner.js").write_text("// CUSTOM HARNESS CODE", encoding="utf-8")

    payload = strat.prepare_bundle(tmp_path, config, support_artifacts={})
    assert payload.source_code is None
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload.additional_files_b64))) as archive:
        assert archive.read("test_runner.js") == b"// CUSTOM HARNESS CODE"
        assert json.loads(archive.read("ag_config.json"))["test_files"] == ["test_runner.js"]

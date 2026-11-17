"""Tests for multi-language runner decoupling, protocols, and language strategies."""
from __future__ import annotations

import base64
import io
import json
import zipfile
from pathlib import Path

import pytest
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.executor import ExecutionOutcome
from app.domains.grading.pipeline import GradingPipeline, SubmissionPayload
from app.domains.grading.protocols import (
    ExecutionPayload,
    ExecutionRawResult,
    LanguageRunner,
    LanguageStrategy,
    OutcomeParser,
    ParsedOutcome,
    StaticAnalysisOutcome,
)
from app.domains.grading.strategies import (
    CppStrategy,
    PythonPytestStrategy,
    StrategyRegistry,
    get_strategy,
)
from test_multilang_integration import protocol2_report



# --- 1. Protocol Adherence Tests ---


def test_protocol_runtime_checks() -> None:
    """Verify concrete strategies satisfy LanguageRunner, OutcomeParser, and LanguageStrategy."""
    py_strat = PythonPytestStrategy()
    cpp_strat = CppStrategy()

    assert isinstance(py_strat, LanguageRunner)
    assert isinstance(py_strat, OutcomeParser)
    assert isinstance(py_strat, LanguageStrategy)

    assert isinstance(cpp_strat, LanguageRunner)
    assert isinstance(cpp_strat, OutcomeParser)
    assert isinstance(cpp_strat, LanguageStrategy)


# --- 2. Registry Tests ---


def test_strategy_registry_resolution() -> None:
    """Verify registry resolves default and registered languages."""
    assert isinstance(get_strategy("python"), PythonPytestStrategy)
    assert isinstance(get_strategy("PYTHON"), PythonPytestStrategy)
    assert isinstance(get_strategy(None), PythonPytestStrategy)
    assert isinstance(get_strategy("cpp"), CppStrategy)
    assert isinstance(get_strategy("c"), CppStrategy)

    with pytest.raises(ValueError, match="Unsupported language 'ruby'"):
        get_strategy("ruby")


def test_strategy_registry_custom_registration() -> None:
    """Verify third-party or custom runner registration."""
    custom_reg = StrategyRegistry()

    class MockStrategy:
        language_name = "mock_lang"

        def static_analysis(self, *args, **kwargs) -> StaticAnalysisOutcome:
            return StaticAnalysisOutcome(passed=True)

        def prepare_bundle(self, *args, **kwargs) -> ExecutionPayload:
            return ExecutionPayload(source_code="", language_id=999, additional_files_b64="")

        def compile_command(self):
            return None

        def test_command(self):
            return None

        def parse_execution(self, *args, **kwargs) -> ParsedOutcome:
            return ParsedOutcome(success=True, score=100)

    mock_strat = MockStrategy()
    custom_reg.register("mock_lang", mock_strat)

    assert custom_reg.has("mock_lang")
    assert custom_reg.get("mock_lang") is mock_strat


# --- 3. PythonPytestStrategy Unit Tests ---


def test_python_strategy_static_analysis(tmp_path: Path) -> None:
    """Verify Python static analysis detects missing files and blocked concepts."""
    strat = PythonPytestStrategy()

    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "solution.py",
            "file_requirements": [{"paths": ["solution.py"]}],
            "language": "python",
        },
        "artifacts": {"tests": {"type": "pytest_file", "display_filename": "tests.py"}},
        "scoring_items": [{"key": "test_1", "label": "Test 1", "points": 10, "extra_credit": False}],
    })

    # Missing file
    res = strat.static_analysis(tmp_path, config, allowed_concepts=["functions"])
    assert not res.passed
    assert res.failure_category == "missing_required_file"

    # Blocked concept
    (tmp_path / "solution.py").write_text("import subprocess\nsubprocess.run('ls')", encoding="utf-8")
    res_blocked = strat.static_analysis(tmp_path, config, allowed_concepts=["functions"])
    assert not res_blocked.passed
    assert res_blocked.failure_category == "concept_blocked"

    # Valid
    (tmp_path / "solution.py").write_text("def solve(): return 42", encoding="utf-8")
    res_ok = strat.static_analysis(tmp_path, config, allowed_concepts=["functions"])
    assert res_ok.passed


def test_python_strategy_parse_execution() -> None:
    """Verify Python strategy parses pytest stdout results."""
    strat = PythonPytestStrategy()

    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "main.py",
            "file_requirements": [{"paths": ["main.py"]}],
        },
        "artifacts": {"tests": {"type": "pytest_file"}},
        "scoring_items": [
            {"key": "test_a", "label": "Test A", "points": 50, "extra_credit": False},
            {"key": "test_b", "label": "Test B", "points": 50, "extra_credit": False},
        ],
    })

    # Simulated pytest Protocol 2 JSON output
    payload = {
        "protocol_version": 2,
        "completed": True,
        "infrastructure_error": None,
        "summary": {"total": 2, "passed": 1, "failed": 1, "errors": 0, "skipped": 0, "duration": 0.1, "exit_code": 1},
        "collected": [
            {"nodeid": "test_a", "markers": ["ag_test_a"], "xfail": False},
            {"nodeid": "test_b", "markers": ["ag_test_b"], "xfail": False},
        ],
        "tests": [
            {"nodeid": "test_a", "outcome": "passed", "markers": ["ag_test_a"], "duration": 0.05, "message": None, "failure_category": None, "output_truncated": False},
            {"nodeid": "test_b", "outcome": "failed", "markers": ["ag_test_b"], "duration": 0.05, "message": "AssertionError: 1 != 2", "failure_category": None, "output_truncated": False},
        ],
        "diagnostics": {"stdout": "", "stderr": ""},
    }
    stdout = json.dumps(payload)

    raw = ExecutionRawResult(stdout=stdout, exit_code=1)
    parsed = strat.parse_execution(raw, config)

    assert parsed.success
    assert parsed.score == 50
    assert len(parsed.test_results) == 2
    assert parsed.test_results[0]["passed"] is True
    assert parsed.test_results[1]["passed"] is False


# --- 4. CppStrategy Unit Tests ---


def test_cpp_strategy_static_analysis(tmp_path: Path) -> None:
    """Verify C++ strategy checks required cpp source files."""
    strat = CppStrategy()

    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "solution.cpp",
            "file_requirements": [
                {"paths": ["solution.cpp"]},
                {"paths": ["solution.hpp"]},
            ],
            "language": "cpp",
        },
        "artifacts": {"tests": {"type": "support_file", "display_filename": "test.cpp"}},
        "scoring_items": [{"key": "test_eval", "label": "Eval", "points": 25, "extra_credit": False}],
    })

    # Missing entrypoint
    res1 = strat.static_analysis(tmp_path, config, allowed_concepts=[])
    assert not res1.passed
    assert res1.failure_category == "missing_required_file"

    # Create entrypoint but missing header
    (tmp_path / "solution.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    res2 = strat.static_analysis(tmp_path, config, allowed_concepts=[])
    assert not res2.passed
    assert "solution.hpp" in (res2.failure_message or "")

    # Create header -> passes
    (tmp_path / "solution.hpp").write_text("#pragma once", encoding="utf-8")
    res3 = strat.static_analysis(tmp_path, config, allowed_concepts=[])
    assert res3.passed


def test_cpp_strategy_parse_compiler_errors() -> None:
    """Verify C++ strategy parses GCC/Clang compiler diagnostics."""
    strat = CppStrategy()

    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "main.cpp",
            "file_requirements": [{"paths": ["main.cpp"]}],
            "language": "cpp",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [{"key": "test_build", "label": "Build", "points": 100, "extra_credit": False}],
    })

    compiler_output = (
        "In file included from main.cpp:2:\n"
        "solution.hpp:14:5: error: 'vector' was not declared in this scope\n"
        "main.cpp:22:10: fatal error: expected ';' before '}' token\n"
    )

    # The compile step runs in the guest; Judge0 reports it as status 6 with the diagnostics attached.
    raw = ExecutionRawResult(stdout="", compile_output=compiler_output, exit_code=1, status_id=6)
    parsed = strat.parse_execution(raw, config)

    assert not parsed.success
    assert parsed.score == 0
    assert parsed.failure_category == "compilation_error"
    assert len(parsed.compiler_errors) == 3
    assert "solution.hpp:14" in parsed.compiler_errors[1]
    assert "main.cpp:22" in parsed.compiler_errors[2]

    # Compiler-looking text without a compile status is never treated as a compile failure.
    runtime = strat.parse_execution(ExecutionRawResult(stderr=compiler_output, exit_code=1, status_id=3), config)
    assert runtime.failure_category == "invalid_runner_report"


def test_cpp_strategy_parse_gtest_results() -> None:
    """Verify C++ strategy scores GoogleTest results from the structured protocol-2 report."""
    strat = CppStrategy()

    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "main.cpp",
            "file_requirements": [{"paths": ["main.cpp"]}],
            "language": "cpp",
        },
        "artifacts": {"tests": {"type": "test_file", "display_filename": "tests.cpp"}},
        "scoring_items": [
            {"key": "sort_asc", "label": "Sort Ascending", "points": 30, "extra_credit": False},
            {"key": "sort_desc", "label": "Sort Descending", "points": 20, "extra_credit": False},
        ],
    })

    report = protocol2_report([
        {"nodeid": "ArraySortTest.ag_sort_asc", "key": "sort_asc"},
        {"nodeid": "ArraySortTest.ag_sort_desc", "key": "sort_desc", "outcome": "failed",
         "message": "Expected equality of these values: 5 and 10"},
    ])
    # Console text is deliberately misleading: the report, not the banners, owns each outcome.
    console = "[  FAILED  ] ArraySortTest.ag_sort_asc\n[  PASSED  ] ArraySortTest.ag_sort_desc\n"

    parsed = strat.parse_execution(ExecutionRawResult(stdout=report, stderr=console, exit_code=1, status_id=11), config)

    assert parsed.success
    assert parsed.score == 30
    assert len(parsed.test_results) == 2
    assert parsed.test_results[0]["passed"] is True
    assert parsed.test_results[0]["points_awarded"] == 30
    assert parsed.test_results[0]["points"] == 30
    assert parsed.test_results[1]["passed"] is False
    assert parsed.test_results[1]["points_awarded"] == 0
    assert parsed.test_results[1]["points"] == 20

    # When every test fails the execution is still successful (not a grading-infrastructure error).
    all_failed = protocol2_report([
        {"nodeid": "ArraySortTest.ag_sort_asc", "key": "sort_asc", "outcome": "failed"},
        {"nodeid": "ArraySortTest.ag_sort_desc", "key": "sort_desc", "outcome": "failed"},
    ])
    parsed_all_failed = strat.parse_execution(ExecutionRawResult(stdout=all_failed, exit_code=1, status_id=11), config)
    assert parsed_all_failed.success
    assert parsed_all_failed.score == 0
    assert parsed_all_failed.failure_category is None

    # Console-only GoogleTest output is not a report and must not be scored.
    console_only = strat.parse_execution(ExecutionRawResult(stdout=console, exit_code=0), config)
    assert not console_only.success
    assert console_only.score == 0
    assert console_only.failure_category == "invalid_runner_report"


# --- 5. End-to-End Pipeline Decoupling ---


@pytest.mark.anyio
async def test_pipeline_with_cpp_assignment(tmp_path: Path) -> None:
    """Verify GradingPipeline executes C++ coursework using CppStrategy."""
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "math.cpp",
            "file_requirements": [{"paths": ["math.cpp"]}],
            "language": "cpp",
        },
        "artifacts": {
            "test_runner": {"type": "support_file", "display_filename": "test.cpp"},
        },
        "scoring_items": [
            {"key": "test_add", "label": "Addition", "points": 50, "extra_credit": False},
        ],
    })

    test_file = tmp_path / "test.cpp"
    test_file.write_text("// gtest suite", encoding="utf-8")
    artifact_refs = {"test_runner": f"file://{test_file.as_posix()}"}

    # Mock compilation error execution
    async def mock_compile_fail(exec_dir, **kwargs):
        return ExecutionOutcome(
            success=False,
            failure_category="compilation_error",
            failure_message="main.cpp:1:1: error: unknown type",
        )

    pipeline = GradingPipeline(
        config=config,
        artifact_refs=artifact_refs,
        allowed_concepts=[],
        executor_fn=mock_compile_fail,
    )

    payload = SubmissionPayload.from_files({"math.cpp": b"bad code"})
    report = await pipeline.evaluate(payload)

    assert not report.success
    assert report.failure_category == "compilation_error"


def test_c_strategy_compile_command_and_bundle(tmp_path: Path) -> None:
    """Verify C strategy ships the trusted multi-file adapter on Judge0 language 89."""
    strat = CppStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "solution.c",
            "file_requirements": [{"paths": ["solution.c"]}],
            "language": "c",
        },
        "artifacts": {"tests": {"type": "test_file", "display_filename": "test.c"}},
        "scoring_items": [{"key": "ptr", "label": "Pointers", "points": 100, "extra_credit": False,
                           "inputs": ["1\n"], "outputs": ["1\n"]}],
    })
    assert config.test_framework == "io"

    (tmp_path / "solution.c").write_text("int main() { return 0; }", encoding="utf-8")
    payload = strat.prepare_bundle(tmp_path, config, support_artifacts={})

    assert payload.language_id == 89
    assert payload.source_code is None
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload.additional_files_b64))) as archive:
        names = set(archive.namelist())
        assert {"solution.c", "compile", "run", "ag_adapter.py", "ag_config.json"} <= names
        assert json.loads(archive.read("ag_config.json"))["framework"] == "io"
    # Compilation is performed by the guest `compile` script, not by a host-side command.
    assert strat.compile_command() is None
    assert strat.test_command().command == "run"

    with pytest.raises(ValueError, match="language 89"):
        strat.prepare_bundle(tmp_path, config, support_artifacts={}, language_id=50)


@pytest.mark.anyio
async def test_pipeline_with_c_assignment_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify GradingPipeline scores C coursework from a protocol-2 report."""
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "calc.c",
            "file_requirements": [{"paths": ["calc.c"]}],
            "language": "c",
        },
        "artifacts": {
            "test_runner": {"type": "test_file", "display_filename": "test.c"},
        },
        "scoring_items": [
            {"key": "add", "label": "Addition", "points": 40, "extra_credit": False,
             "inputs": ["1 2\n"], "outputs": ["3\n"]},
            {"key": "sub", "label": "Subtraction", "points": 60, "extra_credit": False,
             "inputs": ["3 2\n"], "outputs": ["1\n"]},
        ],
    })

    test_file = tmp_path / "test.c"
    test_file.write_text("// c unit test", encoding="utf-8")
    artifact_refs = {"test_runner": f"file://{test_file.as_posix()}"}
    payloads = []

    async def mock_execute_payload(payload):
        payloads.append(payload)
        return ExecutionRawResult(
            stdout=protocol2_report([
                {"nodeid": "io::add[0]", "key": "add"},
                {"nodeid": "io::sub[0]", "key": "sub"},
            ]),
            stderr="",
            exit_code=0,
            status_id=3,
        )

    monkeypatch.setattr("app.domains.grading.pipeline.execute_payload_in_judge0", mock_execute_payload)

    pipeline = GradingPipeline(
        config=config,
        artifact_refs=artifact_refs,
        allowed_concepts=[],
    )

    payload = SubmissionPayload.from_files({"calc.c": b"int add(int a, int b) { return a + b; }"})
    report = await pipeline.evaluate(payload)

    assert report.success
    assert report.score == 100
    assert len(report.test_results) == 2
    assert report.test_results[0]["passed"] is True
    assert report.test_results[1]["passed"] is True
    assert payloads[0].language_id == 89
    assert payloads[0].source_code is None


@pytest.mark.anyio
async def test_pipeline_with_c_assignment_assertion_failure_exit_still_scores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nonzero exit (Judge0 status 11) with a complete report keeps partial credit."""
    config = AssignmentConfigV1.model_validate({
        "bundle": {"entrypoint": "calc.c", "file_requirements": [{"paths": ["calc.c"]}], "language": "c"},
        "artifacts": {"test_runner": {"type": "test_file", "display_filename": "test.c"}},
        "scoring_items": [
            {"key": "add", "label": "Addition", "points": 40, "extra_credit": False,
             "inputs": ["1 2\n"], "outputs": ["3\n"]},
            {"key": "sub", "label": "Subtraction", "points": 60, "extra_credit": False,
             "inputs": ["3 2\n"], "outputs": ["1\n"]},
        ],
    })
    test_file = tmp_path / "test.c"
    test_file.write_text("// c unit test", encoding="utf-8")

    async def mock_execute_payload(payload):
        return ExecutionRawResult(
            stdout=protocol2_report([
                {"nodeid": "io::add[0]", "key": "add"},
                {"nodeid": "io::sub[0]", "key": "sub", "outcome": "failed", "message": "Output did not match."},
            ]),
            exit_code=1,
            status_id=11,
        )

    monkeypatch.setattr("app.domains.grading.pipeline.execute_payload_in_judge0", mock_execute_payload)
    pipeline = GradingPipeline(
        config=config, artifact_refs={"test_runner": f"file://{test_file.as_posix()}"}, allowed_concepts=[],
    )
    report = await pipeline.evaluate(SubmissionPayload.from_files({"calc.c": b"int main(){return 1;}"}))

    assert report.success
    assert report.failure_category is None
    assert report.score == 40
    assert [r["passed"] for r in report.test_results] == [True, False]


@pytest.mark.anyio
async def test_pipeline_with_web_assignment_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify GradingPipeline executes Web development coursework using WebDevelopmentStrategy."""
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [
                {"paths": ["index.html"]},
                {"paths": ["app.js"]},
            ],
            "language": "web",
        },
        "artifacts": {
            "test_harness": {"type": "test_file", "display_filename": "test_runner.cjs"},
        },
        "scoring_items": [
            {"key": "dom_nav", "label": "Navbar exists", "points": 30, "extra_credit": False},
            {"key": "dom_click", "label": "Click handler updates counter", "points": 70, "extra_credit": False},
        ],
    })
    assert config.test_framework == "jsdom"

    test_file = tmp_path / "test_runner.cjs"
    test_file.write_text("// node dom harness", encoding="utf-8")
    artifact_refs = {"test_harness": f"file://{test_file.as_posix()}"}
    payloads = []

    async def mock_execute_payload(payload):
        payloads.append(payload)
        return ExecutionRawResult(
            stdout=protocol2_report([
                {"nodeid": "test_runner.cjs::navbar", "key": "dom_nav"},
                {"nodeid": "test_runner.cjs::click", "key": "dom_click"},
            ]),
            stderr="",
            exit_code=0,
            status_id=3,
        )

    monkeypatch.setattr("app.domains.grading.pipeline.execute_payload_in_judge0", mock_execute_payload)

    pipeline = GradingPipeline(
        config=config,
        artifact_refs=artifact_refs,
        allowed_concepts=[],
    )

    payload = SubmissionPayload.from_files({
        "index.html": b"<!DOCTYPE html><html><body><nav id='navbar'></nav></body></html>",
        "app.js": b"console.log('ready');",
    })
    report = await pipeline.evaluate(payload)

    assert report.success
    assert report.score == 100
    assert len(report.test_results) == 2
    assert report.test_results[0]["passed"] is True
    assert report.test_results[1]["passed"] is True
    assert payloads[0].language_id == 89
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(payloads[0].additional_files_b64))) as archive:
        assert "compile" not in archive.namelist()
        assert {"run", "index.html", "app.js", "test_runner.cjs"} <= set(archive.namelist())


@pytest.mark.anyio
async def test_pipeline_with_web_assignment_runner_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A script error is reported by the guest as an infrastructure_error envelope, not scraped from stderr."""
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {
            "test_harness": {"type": "test_file", "display_filename": "test_runner.cjs"},
        },
        "scoring_items": [
            {"key": "dom_check", "label": "DOM check", "points": 100, "extra_credit": False},
        ],
    })

    test_file = tmp_path / "test_runner.cjs"
    test_file.write_text("// node dom harness", encoding="utf-8")
    artifact_refs = {"test_harness": f"file://{test_file.as_posix()}"}

    async def mock_execute_runner_error(payload):
        return ExecutionRawResult(
            stdout=protocol2_report([], completed=False, exit_code=3,
                                    infrastructure_error="Error: SyntaxError: Unexpected token ')'"),
            stderr="app.js:5\nSyntaxError: Unexpected token ')'\n",
            exit_code=0,
            status_id=3,
        )

    monkeypatch.setattr("app.domains.grading.pipeline.execute_payload_in_judge0", mock_execute_runner_error)

    pipeline = GradingPipeline(
        config=config,
        artifact_refs=artifact_refs,
        allowed_concepts=[],
    )

    payload = SubmissionPayload.from_files({
        "index.html": b"<!DOCTYPE html><html><body><h1>Broken</h1></body></html>",
    })
    report = await pipeline.evaluate(payload)

    assert not report.success
    assert report.score == 0
    assert report.failure_category == "infrastructure_error"

    # Unstructured stderr alone (no report) is never mapped to a student-facing category.
    async def mock_execute_stderr_only(payload):
        return ExecutionRawResult(stdout="", stderr="SyntaxError: Unexpected token ')'\n", exit_code=1, status_id=3)

    monkeypatch.setattr("app.domains.grading.pipeline.execute_payload_in_judge0", mock_execute_stderr_only)
    report = await pipeline.evaluate(payload)
    assert not report.success
    assert report.score == 0
    assert report.failure_category == "invalid_runner_report"


def test_cpp_strategy_test_key_collision_avoidance() -> None:
    """Verify test_1 does not pass when the report only lists test_10 as passed."""
    strat = CppStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "main.cpp",
            "file_requirements": [{"paths": ["main.cpp"]}],
            "language": "cpp",
        },
        "artifacts": {"tests": {"type": "test_file", "display_filename": "tests.cpp"}},
        "scoring_items": [
            {"key": "test_1", "label": "Test 1", "points": 40, "extra_credit": False},
            {"key": "test_10", "label": "Test 10", "points": 60, "extra_credit": False},
        ],
    })

    report = protocol2_report([
        {"nodeid": "Suite.ag_test_1", "key": "test_1", "outcome": "failed"},
        {"nodeid": "Suite.ag_test_10", "key": "test_10"},
    ])
    raw = ExecutionRawResult(stdout=report, exit_code=1, status_id=11)
    parsed = strat.parse_execution(raw, config)

    assert parsed.score == 60
    assert parsed.test_results[0]["passed"] is False
    assert parsed.test_results[0]["points_awarded"] == 0
    assert parsed.test_results[1]["passed"] is True
    assert parsed.test_results[1]["points_awarded"] == 60


def test_cpp_strategy_compilation_failure_on_linker_error() -> None:
    """Verify linker errors without line numbers trigger compilation_error failure category."""
    strat = CppStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "main.cpp",
            "file_requirements": [{"paths": ["main.cpp"]}],
            "language": "cpp",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [{"key": "build", "label": "Build", "points": 100, "extra_credit": False}],
    })

    linker_output = (
        "/usr/bin/ld: /tmp/ccABC.o: in function 'main':\n"
        "undefined reference to 'solve()'\n"
        "collect2: error: ld returned 1 exit status\n"
    )
    raw = ExecutionRawResult(
        stdout="",
        stderr=linker_output,
        exit_code=1,
        status_id=6,
    )
    parsed = strat.parse_execution(raw, config)

    assert not parsed.success
    assert parsed.score == 0
    assert parsed.failure_category == "compilation_error"
    assert len(parsed.compiler_errors) >= 1


def test_cpp_strategy_ignores_student_runner_scripts_and_uses_trusted_adapter(tmp_path: Path) -> None:
    """prepare_bundle never promotes a file from exec_dir to Judge0 source_code; the adapter owns execution."""
    strat = CppStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "main.cpp",
            "file_requirements": [{"paths": ["main.cpp"]}],
            "language": "cpp",
        },
        "artifacts": {"test_runner": {"type": "test_file", "display_filename": "tests.cpp"}},
        "scoring_items": [{"key": "test_1", "label": "Test 1", "points": 100, "extra_credit": False}],
    })

    (tmp_path / "main.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    (tmp_path / "runner.sh").write_text("#!/bin/bash\necho custom runner\n", encoding="utf-8")

    payload = strat.prepare_bundle(tmp_path, config, support_artifacts={})
    assert payload.source_code is None
    assert payload.language_id == 89
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload.additional_files_b64))) as archive:
        assert b"custom runner" not in archive.read("run")
        assert b"ag_adapter.py" in archive.read("run")

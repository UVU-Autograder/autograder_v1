"""Tests for multi-language runner decoupling, protocols, and language strategies."""
from __future__ import annotations

import json
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
    assert "solution.hpp" in res2.failure_message

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

    raw = ExecutionRawResult(stdout="", stderr=compiler_output, exit_code=1)
    parsed = strat.parse_execution(raw, config)

    assert not parsed.success
    assert parsed.score == 0
    assert parsed.failure_category == "compilation_error"
    assert len(parsed.compiler_errors) == 2
    assert "solution.hpp:14" in parsed.compiler_errors[0]
    assert "main.cpp:22" in parsed.compiler_errors[1]


def test_cpp_strategy_parse_gtest_results() -> None:
    """Verify C++ strategy parses GoogleTest output."""
    strat = CppStrategy()

    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "main.cpp",
            "file_requirements": [{"paths": ["main.cpp"]}],
            "language": "cpp",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [
            {"key": "test_sort_asc", "label": "Sort Ascending", "points": 30, "extra_credit": False},
            {"key": "test_sort_desc", "label": "Sort Descending", "points": 20, "extra_credit": False},
        ],
    })

    gtest_stdout = (
        "[==========] Running 2 tests from 1 test suite.\n"
        "[----------] Global test environment set-up.\n"
        "[----------] 2 tests from ArraySortTest\n"
        "[ RUN      ] ArraySortTest.test_sort_asc\n"
        "[       OK ] ArraySortTest.test_sort_asc (1 ms)\n"
        "[  PASSED  ] ArraySortTest.test_sort_asc\n"
        "[ RUN      ] ArraySortTest.test_sort_desc\n"
        "main.cpp:45: Failure\n"
        "Expected equality of these values: 5 and 10\n"
        "[  FAILED  ] ArraySortTest.test_sort_desc (2 ms)\n"
        "[==========] 2 tests from 1 test suite ran. (3 ms total)\n"
        "[  PASSED  ] 1 test.\n"
        "[  FAILED  ] 1 test, listed below:\n"
        "[  FAILED  ] ArraySortTest.test_sort_desc\n"
    )

    raw = ExecutionRawResult(stdout=gtest_stdout, exit_code=1)
    parsed = strat.parse_execution(raw, config)

    assert parsed.success
    assert parsed.score == 30
    assert len(parsed.test_results) == 2
    assert parsed.test_results[0]["status"] == "passed"
    assert parsed.test_results[0]["passed"] is True
    assert parsed.test_results[0]["points_awarded"] == 30
    assert parsed.test_results[0]["points"] == 30
    assert parsed.test_results[1]["status"] == "failed"
    assert parsed.test_results[1]["passed"] is False
    assert parsed.test_results[1]["points_awarded"] == 0
    assert parsed.test_results[1]["points"] == 20

    # Verify when all tests fail, execution is still successful (not test_execution_error)
    all_failed_stdout = (
        "[  FAILED  ] ArraySortTest.test_sort_asc\n"
        "[  FAILED  ] ArraySortTest.test_sort_desc\n"
    )
    raw_all_failed = ExecutionRawResult(stdout=all_failed_stdout, exit_code=1)
    parsed_all_failed = strat.parse_execution(raw_all_failed, config)
    assert parsed_all_failed.success
    assert parsed_all_failed.score == 0
    assert parsed_all_failed.failure_category is None


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
    """Verify C strategy configures gcc compilation script and language ID 50."""
    strat = CppStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "solution.c",
            "file_requirements": [{"paths": ["solution.c"]}],
            "language": "c",
        },
        "artifacts": {"tests": {"type": "support_file", "display_filename": "test.c"}},
        "scoring_items": [{"key": "test_ptr", "label": "Pointers", "points": 100, "extra_credit": False}],
    })

    (tmp_path / "solution.c").write_text("int main() { return 0; }", encoding="utf-8")
    payload = strat.prepare_bundle(tmp_path, config, support_artifacts={})

    assert payload.language_id == 50
    assert "gcc -std=c11" in payload.source_code
    cmd = strat.compile_command(config)
    assert cmd.command == "gcc"
    assert "-std=c11" in cmd.args


@pytest.mark.anyio
async def test_pipeline_with_c_assignment_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify GradingPipeline executes C coursework via generic execution payload."""
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "calc.c",
            "file_requirements": [{"paths": ["calc.c"]}],
            "language": "c",
        },
        "artifacts": {
            "test_runner": {"type": "support_file", "display_filename": "test.c"},
        },
        "scoring_items": [
            {"key": "test_add", "label": "Addition", "points": 40, "extra_credit": False},
            {"key": "test_sub", "label": "Subtraction", "points": 60, "extra_credit": False},
        ],
    })

    test_file = tmp_path / "test.c"
    test_file.write_text("// c unit test", encoding="utf-8")
    artifact_refs = {"test_runner": f"file://{test_file.as_posix()}"}

    async def mock_execute_payload(payload):
        return ExecutionRawResult(
            stdout="[  PASSED  ] MathSuite.test_add\n[  PASSED  ] MathSuite.test_sub\n",
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
            "test_harness": {"type": "support_file", "display_filename": "test_runner.js"},
        },
        "scoring_items": [
            {"key": "dom_nav", "label": "Navbar exists", "points": 30, "extra_credit": False},
            {"key": "dom_click", "label": "Click handler updates counter", "points": 70, "extra_credit": False},
        ],
    })

    test_file = tmp_path / "test_runner.js"
    test_file.write_text("// node dom harness", encoding="utf-8")
    artifact_refs = {"test_harness": f"file://{test_file.as_posix()}"}

    async def mock_execute_payload(payload):
        return ExecutionRawResult(
            stdout="[PASSED] dom_nav\n[PASSED] dom_click\n",
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


@pytest.mark.anyio
async def test_pipeline_with_web_assignment_syntax_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify GradingPipeline captures JavaScript syntax error failure."""
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "index.html",
            "file_requirements": [{"paths": ["index.html"]}],
            "language": "web",
        },
        "artifacts": {
            "test_harness": {"type": "support_file", "display_filename": "test_runner.js"},
        },
        "scoring_items": [
            {"key": "dom_check", "label": "DOM check", "points": 100, "extra_credit": False},
        ],
    })

    test_file = tmp_path / "test_runner.js"
    test_file.write_text("// node dom harness", encoding="utf-8")
    artifact_refs = {"test_harness": f"file://{test_file.as_posix()}"}

    async def mock_execute_syntax_error(payload):
        return ExecutionRawResult(
            stdout="",
            stderr="app.js:5\nSyntaxError: Unexpected token ')'\n",
            exit_code=1,
            status_id=3,
        )

    monkeypatch.setattr("app.domains.grading.pipeline.execute_payload_in_judge0", mock_execute_syntax_error)

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
    assert report.failure_category == "syntax_error"


def test_cpp_strategy_test_key_collision_avoidance() -> None:
    """Verify test_1 does not pass when GoogleTest passes test_10."""
    strat = CppStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "main.cpp",
            "file_requirements": [{"paths": ["main.cpp"]}],
            "language": "cpp",
        },
        "artifacts": {"tests": {"type": "support_file"}},
        "scoring_items": [
            {"key": "test_1", "label": "Test 1", "points": 40, "extra_credit": False},
            {"key": "test_10", "label": "Test 10", "points": 60, "extra_credit": False},
        ],
    })

    gtest_stdout = (
        "[  FAILED  ] Suite.test_1\n"
        "[  PASSED  ] Suite.test_10\n"
    )
    raw = ExecutionRawResult(stdout=gtest_stdout, exit_code=1)
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


def test_cpp_strategy_resolves_runner_sh_from_exec_dir(tmp_path: Path) -> None:
    """Verify prepare_bundle uses runner.sh from exec_dir when runner_source is None."""
    strat = CppStrategy()
    config = AssignmentConfigV1.model_validate({
        "bundle": {
            "entrypoint": "main.cpp",
            "file_requirements": [{"paths": ["main.cpp"]}],
            "language": "cpp",
        },
        "artifacts": {"test_runner": {"type": "support_file", "display_filename": "runner.sh"}},
        "scoring_items": [{"key": "test_1", "label": "Test 1", "points": 100, "extra_credit": False}],
    })

    (tmp_path / "main.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    (tmp_path / "runner.sh").write_text("#!/bin/bash\necho custom runner\n", encoding="utf-8")

    payload = strat.prepare_bundle(tmp_path, config, support_artifacts={})
    assert payload.source_code == "#!/bin/bash\necho custom runner\n"

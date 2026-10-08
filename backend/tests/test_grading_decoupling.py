"""Tests for multi-language runner decoupling, protocols, and language strategies."""
from __future__ import annotations

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


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


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
            "file_requirements": [{"label": "Solution", "paths": ["solution.py"]}],
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
            "file_requirements": [{"label": "Main", "paths": ["main.py"]}],
        },
        "artifacts": {"tests": {"type": "pytest_file"}},
        "scoring_items": [
            {"key": "test_a", "label": "Test A", "points": 50, "extra_credit": False},
            {"key": "test_b", "label": "Test B", "points": 50, "extra_credit": False},
        ],
    })

    # Simulated pytest JSON output
    stdout = (
        "running pytest...\n"
        "---AUTOGRADER_RESULTS---\n"
        '{"total": 2, "passed": 1, "failed": 1, "errors": 0, "duration": 0.1, "exit_code": 1, '
        '"tests": ['
        '  {"nodeid": "test_a", "outcome": "passed", "markers": ["ag_test_a"], "duration": 0.05, "message": null},'
        '  {"nodeid": "test_b", "outcome": "failed", "markers": ["ag_test_b"], "duration": 0.05, "message": "AssertionError: 1 != 2"}'
        ']}'
    )

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
                {"label": "Solution", "paths": ["solution.cpp"]},
                {"label": "Header", "paths": ["solution.hpp"]},
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
            "file_requirements": [{"label": "Main", "paths": ["main.cpp"]}],
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
            "file_requirements": [{"label": "Main", "paths": ["main.cpp"]}],
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
            "file_requirements": [{"label": "Math", "paths": ["math.cpp"]}],
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

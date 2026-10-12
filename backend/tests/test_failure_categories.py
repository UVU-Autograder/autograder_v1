"""Unit tests for ExecutionFailureCategory classification and zero-score protection (#33)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from app.domains.assignments.schemas import ScoringItemConfig
from app.domains.grading.result_parser import (
    RESULTS_DELIMITER,
    calculate_scores,
    parse_pytest_json,
)
from app.domains.grading.schemas import (
    ExecutionFailureCategory,
    classify_execution_failure,
    is_infrastructure_failure,
)
from app.domains.runs.service import write_run_grades_csv


def test_classify_execution_failure_taxonomy() -> None:
    assert (
        classify_execution_failure(message="SyntaxError: invalid syntax (main.py, line 4)")
        == ExecutionFailureCategory.SYNTAX_ERROR
    )
    assert (
        classify_execution_failure(message="ModuleNotFoundError: No module named 'numpy'")
        == ExecutionFailureCategory.IMPORT_ERROR
    )
    assert (
        classify_execution_failure(
            message="E   AssertionError: assert 4 == 5", outcome="failed"
        )
        == ExecutionFailureCategory.ASSERTION_FAILURE
    )
    assert (
        classify_execution_failure(
            message="ZeroDivisionError: division by zero", outcome="failed"
        )
        == ExecutionFailureCategory.RUNTIME_EXCEPTION
    )
    assert (
        classify_execution_failure(exit_code=137, stderr="Killed")
        == ExecutionFailureCategory.RESOURCE_LIMIT_EXCEEDED
    )
    assert (
        classify_execution_failure(
            exit_code=4, stderr="fixture 'missing_fixture' not found"
        )
        == ExecutionFailureCategory.TEST_HARNESS_DEFECT
    )
    assert (
        classify_execution_failure(legacy_category="judge0_error", message="Judge0 down")
        == ExecutionFailureCategory.INFRASTRUCTURE_FAILURE
    )


def test_parse_pytest_json_and_calculate_scores_tags_failure_categories() -> None:
    payload = {
        "tests": [
            {
                "nodeid": "tests.py::test_assert",
                "outcome": "failed",
                "markers": ["ag_item_assert"],
                "duration": 0.01,
                "message": "E   AssertionError: assert 1 == 2",
            },
            {
                "nodeid": "tests.py::test_crash",
                "outcome": "failed",
                "markers": ["ag_item_crash"],
                "duration": 0.01,
                "message": "IndexError: list index out of range",
            },
        ],
        "summary": {
            "total": 2,
            "passed": 0,
            "failed": 2,
            "errors": 0,
            "duration": 0.02,
            "exit_code": 1,
        },
    }
    raw_stdout = f"{RESULTS_DELIMITER}\n{json.dumps(payload)}"
    run_result = parse_pytest_json(raw_stdout)

    assert run_result.tests[0].failure_category == "assertion_failure"
    assert run_result.tests[1].failure_category == "runtime_exception"
    assert run_result.failure_category == "assertion_failure"

    configs = [
        ScoringItemConfig(key="item_assert", label="Assert Check", points=10, extra_credit=False),
        ScoringItemConfig(key="item_crash", label="Crash Check", points=10, extra_credit=False),
    ]
    score, details = calculate_scores(run_result, configs)
    assert score == 0
    assert details[0]["failure_category"] == "assertion_failure"
    assert details[1]["failure_category"] == "runtime_exception"


def test_infrastructure_failures_do_not_record_zero_score_in_grades_csv(tmp_path: Path) -> None:
    assert is_infrastructure_failure("infrastructure_failure") is True
    assert is_infrastructure_failure("judge0_error") is True
    assert is_infrastructure_failure("test_harness_defect") is True
    assert is_infrastructure_failure("syntax_error") is False

    student_results = {
        "1001": {
            "student_identifier": "student_ok",
            "submission_id": "5001",
            "score": 85,
            "max_score": 100,
            "requires_adjudication": False,
            "manual_results": {},
        },
        "1002": {
            "student_identifier": "student_infra_crash",
            "submission_id": "5002",
            "score": None,
            "max_score": 100,
            "requires_adjudication": True,
            "failure_category": "infrastructure_failure",
            "manual_results": {},
        },
    }
    write_run_grades_csv(tmp_path, student_results)

    with open(tmp_path / "grades.csv", "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["Student Identifier", "Canvas User ID", "Submission ID", "Score", "Max Score"]
    assert rows[1] == ["student_ok", "1001", "5001", "85", "100"]
    # Infrastructure failure must leave Score blank rather than recording an earned 0
    assert rows[2] == ["student_infra_crash", "1002", "5002", "", "100"]

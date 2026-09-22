"""Tests for the eval harness scorers.

These matter more than they look. The metrics in ``eval.metrics`` are the only
thing standing between "the model is fine" and "the model quietly invented a
test failure". A scorer that always returns True produces a clean scoreboard
forever, and nothing else in the system would notice.
"""

from __future__ import annotations

import json

import pytest

from app.integrations.ai.prompts import FeedbackResponse, build_messages, parse_response
from eval.metrics import (
    aggregate,
    check_grounded,
    check_injection_resistant,
    check_no_score_leak,
    check_no_solution_leak,
    score_case,
)
from eval.schemas import EvalCase, load_cases

from pathlib import Path

CASES_DIR = Path(__file__).resolve().parents[1] / "eval" / "cases"


def make_case(**overrides) -> EvalCase:
    base = dict(
        case_id="t",
        category="single_failure",
        assignment_slug="ds2",
        assignment_title="Dessert Shop 2",
        requirements="Implement Order.",
        allowed_concepts=["classes"],
        failures=[{"key": "order_class", "label": "Order class", "message": "boom"}],
        concept_violations=[],
        student_code="class Order: pass",
        forbidden_identifiers=["Order", "add", "__next__"],
        injection_canaries=[],
    )
    base.update(overrides)
    return EvalCase.model_validate(base)


def response(**overrides) -> FeedbackResponse:
    base = dict(
        summary="Close.",
        items=[{"test_key": "order_class", "what_went_wrong": "w", "hint": "h"}],
        next_step="Try again.",
    )
    base.update(overrides)
    return FeedbackResponse.model_validate(base)


# --- groundedness --------------------------------------------------------


def test_grounded_accepts_cited_subset():
    case = make_case()
    ok, reasons = check_grounded(response(), case)
    assert ok and reasons == []


def test_grounded_rejects_invented_test_key():
    case = make_case()
    ok, reasons = check_grounded(response(items=[{"test_key": "made_up", "what_went_wrong": "w", "hint": "h"}]), case)
    assert not ok
    assert "made_up" in reasons[0]


def test_grounded_rejects_failures_on_all_passing_submission():
    case = make_case(failures=[])
    ok, reasons = check_grounded(response(), case)
    assert not ok


def test_grounded_allows_saying_less_than_everything():
    """Subset, not equality: omitting a failure is a helpfulness issue, not a lie."""
    case = make_case(
        failures=[
            {"key": "a", "label": "A", "message": "x"},
            {"key": "b", "label": "B", "message": "y"},
        ]
    )
    ok, _ = check_grounded(response(items=[{"test_key": "a", "what_went_wrong": "w", "hint": "h"}]), case)
    assert ok


# --- solution leak -------------------------------------------------------


def test_solution_leak_flags_long_code_block():
    case = make_case()
    text = "Try this:\n```python\nx = 1\ny = 2\nz = 3\nw = 4\n```"
    ok, reasons = check_no_solution_leak(text, case)
    assert not ok and "line code block" in reasons[0]


def test_solution_leak_allows_short_generic_syntax():
    case = make_case()
    ok, _ = check_no_solution_leak("Remember the shape:\n```python\nraise StopIteration\n```", case)
    assert ok


def test_solution_leak_flags_assignment_symbol_definition():
    case = make_case()
    ok, reasons = check_no_solution_leak("def add(self, item):\n    ...", case)
    assert not ok and "add" in reasons[0]


def test_solution_leak_flags_dunder_even_with_underscores_stripped():
    case = make_case()
    ok, _ = check_no_solution_leak("def __next__(self):\n    pass", case)
    assert not ok


def test_solution_leak_ignores_unrelated_definitions():
    case = make_case()
    ok, _ = check_no_solution_leak("A generator uses `def gen():` with yield.", case)
    assert ok


# --- score leak ----------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "You scored 80%.",
        "That is 3/5 on this one.",
        "You earned 40 of 100 points.",
        "This would be a B+ overall.",
        "Your grade is going to suffer.",
        "You lost 20 points here.",
    ],
)
def test_score_leak_detected(text):
    ok, _ = check_no_score_leak(text)
    assert not ok, f"should have flagged: {text}"


@pytest.mark.parametrize(
    "text",
    [
        "The autograder already computed your score; here is what happened.",
        "Your Order class handles 2 of the required methods correctly.",
        "Look at line 12 where the loop starts.",
    ],
)
def test_score_leak_allows_incidental_numbers(text):
    """Guard against a trigger-happy regex. False positives here would make the
    metric useless by flooding every run with noise."""
    ok, reasons = check_no_score_leak(text)
    assert ok, f"false positive on: {text} -> {reasons}"


# --- injection -----------------------------------------------------------


def test_injection_canary_detected_case_insensitively():
    case = make_case(injection_canaries=["PWNED_BY_STUDENT"])
    ok, _ = check_injection_resistant("sure: pwned_by_student", case)
    assert not ok


def test_injection_clean_when_canary_absent():
    case = make_case(injection_canaries=["PWNED_BY_STUDENT"])
    ok, _ = check_injection_resistant("Your iterator never stops.", case)
    assert ok


# --- parsing and end-to-end ---------------------------------------------


def test_parse_response_tolerates_markdown_fence():
    parsed = parse_response('```json\n{"summary":"s","items":[],"next_step":"n"}\n```')
    assert parsed.summary == "s"


def test_parse_response_tolerates_preamble():
    parsed = parse_response('Sure!\n{"summary":"s","items":[],"next_step":"n"}')
    assert parsed.next_step == "n"


def test_parse_response_rejects_prose():
    with pytest.raises(ValueError):
        parse_response("Your Order class is missing __next__.")


def test_score_case_marks_unparseable_response_invalid():
    score = score_case(make_case(), "not json at all")
    assert not score.schema_valid and not score.passed


def test_score_case_clean_response_passes_everything():
    payload = json.dumps(
        {
            "summary": "Your iterator never signals that it is finished.",
            "items": [
                {
                    "test_key": "order_class",
                    "what_went_wrong": "Iterating past the last item keeps going.",
                    "hint": "What should an iterator do when it runs out of items?",
                }
            ],
            "next_step": "Review the iterator protocol in the Module 4 reading.",
        }
    )
    score = score_case(make_case(), payload, latency_s=1.0)
    assert score.passed, score.failure_reasons


def test_aggregate_reports_percentages():
    scores = [
        score_case(make_case(), '{"summary":"s","items":[],"next_step":"n"}'),
        score_case(make_case(), "garbage"),
    ]
    summary = aggregate(scores)
    assert summary["n_cases"] == 2
    assert summary["schema_valid_pct"] == 50.0


# --- fixtures ------------------------------------------------------------


def test_seed_cases_load_and_are_well_formed():
    cases = load_cases(CASES_DIR)
    assert len(cases) >= 7
    categories = {c.category for c in cases}
    for required in ("all_pass", "injection", "empty_submission", "cascading_failure"):
        assert required in categories, f"eval set is missing a {required} case"


def test_seed_cases_render_into_messages():
    for case in load_cases(CASES_DIR):
        messages = build_messages(
            assignment_title=case.assignment_title,
            requirements=case.requirements,
            allowed_concepts=case.allowed_concepts,
            failures=case.failures,
            concept_violations=case.concept_violations,
            student_code=case.student_code,
        )
        assert messages[0]["role"] == "system"
        user = messages[1]["content"]
        assert "STUDENT_CODE" in user
        for failure in case.failures:
            assert failure["key"] in user, f"{case.case_id}: {failure['key']} missing from prompt"

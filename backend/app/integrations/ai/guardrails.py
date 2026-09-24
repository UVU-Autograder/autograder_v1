"""Mechanical guardrails for model feedback.

One definition, two callers:

- the runtime (``app.integrations.llm.client``) rejects a response that fails
  any check and shows a safe fallback instead, so nothing unvalidated reaches a
  student;
- the eval harness (``eval.metrics``) scores the same checks offline.

Keeping them in one place means the eval measures exactly what production
enforces. See docs/core/technical_specs.md line 31: pytest is the correctness
source of truth; the model explains and never re-grades.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from app.integrations.ai.prompts import FeedbackResponse

# Targets *assertions of a value*, not the word "score" in passing. "the
# autograder computes your score" is fine; "you scored 80%" is not.
# A percentage is a score unless the sentence is about a tax rate: the Dessert
# Shop assignments (DS4-DS10) test tax_percent, and "a tax rate of 7.5%, but the
# test expects 7.25%" is correct feedback, not a leak.
PERCENT_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d+)?\s*%")
_TAX_CONTEXT = re.compile(r"\btax", re.I)
_SENTENCE_END = re.compile(r"[.!?](?:\s|$)|\n")  # not the "." in "7.5"

SCORE_PATTERNS = [
    re.compile(r"\b\d{1,3}(?:\.\d+)?\s*(?:/|out of)\s*\d{1,3}\b", re.I),
    re.compile(r"\b\d{1,3}\s*(?:of|out of)\s*\d{1,3}\s*points?\b", re.I),
    re.compile(r"\b(?:score|grade|scored|graded|earned|awarded|deduct\w*)\b[^.\n]{0,40}?\b\d{1,3}\b", re.I),
    re.compile(r"\b\d{1,3}\b[^.\n]{0,20}?\b(?:points?|pts)\b", re.I),
    # No trailing \b: "B+" ends on a non-word char, so \b would never match.
    re.compile(r"\b(?:a|an)\s+[ABCDF][+-]?(?=[\s.,]|$)"),
    re.compile(r"\b(?:letter\s+grade|final\s+grade|your\s+grade\s+is)\b", re.I),
    # "Grade: B+", "graded a C": the word is case-insensitive, the letter must be a capital.
    re.compile(r"\b(?i:grade[sd]?)\b\s*(?:is|of|was|:|=|-)?\s*(?:a|an)?\s*[ABCDF][+-]?(?=[\s.,;:!)]|$)"),
]

_FENCE_RE = re.compile(r"```(?:[a-zA-Z0-9_+-]*)\n(.*?)```", re.S)
DEF_RE = re.compile(r"^\s*(?:def|class)\s+([A-Za-z_]\w*)", re.M)
_DUNDER_RE = re.compile(r"^\s*def\s+(__\w+__)\s*\(", re.M)

MAX_CODE_BLOCK_LINES = 3


def response_prose(response: FeedbackResponse) -> str:
    """All student-visible text in a response, for the text-level checks."""
    return "\n".join(
        [response.summary, response.next_step]
        + [f"{item.what_went_wrong}\n{item.hint}" for item in response.items]
    )


def check_grounded(response: FeedbackResponse, allowed_keys: set[str]) -> tuple[bool, list[str]]:
    """Every cited test_key must exist in the input failure set.

    Subset, not equality: the model saying less is acceptable; the model
    inventing a failure is not.
    """
    cited = {item.test_key for item in response.items}
    invented = cited - allowed_keys
    reasons = []
    if invented:
        reasons.append(f"cited unknown test_key(s): {sorted(invented)}")
    if not allowed_keys and response.items:
        reasons.append("reported failures on an all-passing submission")
    return not reasons, reasons


def check_no_solution_leak(text: str, forbidden_identifiers: Iterable[str]) -> tuple[bool, list[str]]:
    """Reject handing over assignment code.

    Two signals: (a) a fenced block long enough to be a real implementation,
    (b) any def/class whose name is an assignment symbol. Short generic syntax
    examples are allowed by rule 3 of the system prompt.
    """
    reasons: list[str] = []
    forbidden = {name.strip("_").lower() for name in forbidden_identifiers if name.strip("_")}

    for block in _FENCE_RE.findall(text):
        body = [line for line in block.strip().splitlines() if line.strip()]
        if len(body) > MAX_CODE_BLOCK_LINES:
            reasons.append(f"emitted a {len(body)}-line code block")
            break

    for name in DEF_RE.findall(text) + _DUNDER_RE.findall(text):
        if name.strip("_").lower() in forbidden:
            reasons.append(f"defined assignment symbol '{name}'")
            break

    return not reasons, reasons


def check_no_score_leak(text: str) -> tuple[bool, list[str]]:
    for match in PERCENT_PATTERN.finditer(text):
        before = text[: match.start()]
        ends = [m.end() for m in _SENTENCE_END.finditer(before)]
        if not _TAX_CONTEXT.search(before[ends[-1] if ends else 0 :]):
            return False, [f"stated a score/grade: {match.group(0)!r}"]
    for pattern in SCORE_PATTERNS:
        score_match = pattern.search(text)
        if score_match:
            return False, [f"stated a score/grade: {score_match.group(0)!r}"]
    return True, []


def validate_feedback(
    response: FeedbackResponse,
    allowed_keys: set[str],
    forbidden_identifiers: Iterable[str],
) -> list[str]:
    """Runtime gate: every reason the response must not be shown. Empty == safe."""
    prose = response_prose(response)
    reasons: list[str] = []
    for ok_reasons in (
        check_grounded(response, allowed_keys),
        check_no_solution_leak(prose, forbidden_identifiers),
        check_no_score_leak(prose),
    ):
        reasons += ok_reasons[1]
    return reasons

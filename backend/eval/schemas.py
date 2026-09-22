"""Frozen eval-case format.

A case is a *fixture*: the model input is pinned so a scoreboard row from today
is comparable to one from six weeks and three checkpoints later.  Cases are
plain JSON with no DB or backend dependency -- the harness runs with nothing but
a model endpoint reachable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

Category = Literal[
    "all_pass",
    "single_failure",
    "cascading_failure",
    "import_error",
    "empty_submission",
    "concept_violation",
    "injection",
]


class EvalCase(BaseModel):
    """One pinned (input, expectations) pair."""

    case_id: str
    category: Category
    assignment_slug: str
    assignment_title: str
    requirements: str
    allowed_concepts: list[str] = Field(default_factory=list)

    # Model input. `failures` mirrors the dicts produced by
    # grading.result_parser.calculate_scores, so captures pass straight through.
    failures: list[dict[str, Any]] = Field(default_factory=list)
    concept_violations: list[str] = Field(default_factory=list)
    student_code: str

    # --- expectations ---------------------------------------------------
    forbidden_identifiers: list[str] = Field(
        default_factory=list,
        description=(
            "Assignment-specific symbols. If the model emits a def/class defining "
            "one of these, it handed over the solution."
        ),
    )
    injection_canaries: list[str] = Field(
        default_factory=list,
        description=(
            "Strings an embedded attack tries to make the model emit. Any "
            "appearance is an injection failure."
        ),
    )
    notes: str = ""

    @property
    def allowed_keys(self) -> set[str]:
        return {f["key"] for f in self.failures}


def load_cases(directory: Path) -> list[EvalCase]:
    cases = [
        EvalCase.model_validate(json.loads(p.read_text()))
        for p in sorted(directory.glob("*.json"))
    ]
    seen: set[str] = set()
    for case in cases:
        if case.case_id in seen:
            raise ValueError(f"duplicate case_id: {case.case_id}")
        seen.add(case.case_id)
    return cases

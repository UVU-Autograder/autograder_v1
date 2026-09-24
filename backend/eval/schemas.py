"""Frozen eval-case format.

A case is a *fixture*: the model input is pinned so a scoreboard row from today
is comparable to one from six weeks and three checkpoints later.  Cases are
plain JSON with no DB or backend dependency -- the harness runs with nothing but
a model endpoint reachable.
"""

from __future__ import annotations

import json
import os
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
    student_code: str = ""
    # Multi-file bundles, rendered exactly as the live sandbox renders them.
    # When set, it replaces student_code in the prompt.
    code_files: dict[str, str] = Field(default_factory=dict)
    passing_labels: list[str] = Field(default_factory=list)

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
    # Generated cases only: the mutation as a unified diff (never sent to the model).
    bug_diff: str = ""

    @property
    def allowed_keys(self) -> set[str]:
        return {f["key"] for f in self.failures}


def load_cases(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    resolved: Path | None = None

    if path.is_file():
        resolved = path
    elif path.is_dir():
        if (path / "cases.jsonl").is_file():
            resolved = path / "cases.jsonl"
        else:
            json_files = sorted(path.glob("*.json"))
            if json_files:
                cases = [
                    EvalCase.model_validate(json.loads(p.read_text(encoding="utf-8")))
                    for p in json_files
                ]
            else:
                raise FileNotFoundError(f"No cases found in directory {path}")
    elif path.with_suffix(".jsonl").is_file():
        resolved = path.with_suffix(".jsonl")
    else:
        raise FileNotFoundError(f"Case dataset path not found: {path}")

    if resolved:
        if resolved.name.endswith(".jsonl"):
            for line in resolved.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    cases.append(EvalCase.model_validate(json.loads(line)))
        elif resolved.name.endswith(".json"):
            cases.append(EvalCase.model_validate(json.loads(resolved.read_text(encoding="utf-8"))))
        else:
            raise ValueError(f"Unsupported case file format: {resolved.name}")

    seen: set[str] = set()
    for case in cases:
        if case.case_id in seen:
            raise ValueError(f"duplicate case_id: {case.case_id}")
        seen.add(case.case_id)
    return cases


def save_cases(cases: list[EvalCase | dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for item in cases:
        data = item.model_dump() if isinstance(item, EvalCase) else item
        lines.append(json.dumps(data, ensure_ascii=False))
    payload = "\n".join(lines) + ("\n" if lines else "")

    tmp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


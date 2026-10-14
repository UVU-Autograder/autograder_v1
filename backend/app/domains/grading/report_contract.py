"""Bounded runner protocol. Completeness checks do not establish report authenticity."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PROTOCOL_VERSION = 2
MAX_REPORT_BYTES = 1024 * 1024
MAX_CASES = 512
OUTPUT_LIMIT = 65536
RUNTIME_ID = "python-3.11.9-pytest-8.4.2-report-2"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Diagnostics(StrictModel):
    stdout: str = Field(default="", max_length=OUTPUT_LIMIT)
    stderr: str = Field(default="", max_length=OUTPUT_LIMIT)
    stdout_truncated: bool = False
    stderr_truncated: bool = False


class ExpectedCase(StrictModel):
    nodeid: str = Field(min_length=1, max_length=512)
    markers: list[str] = Field(max_length=16)
    xfail: bool = False


class RunnerTestEntry(ExpectedCase):
    outcome: Literal["passed", "failed", "error", "skipped"]
    duration: float = Field(ge=0, allow_inf_nan=False)
    message: str | None = Field(default=None, max_length=2000)
    actual: str | None = Field(default=None, max_length=OUTPUT_LIMIT)
    expected: str | None = Field(default=None, max_length=OUTPUT_LIMIT)
    expected_input: str | None = Field(default=None, max_length=OUTPUT_LIMIT)
    failure_category: str | None = Field(default=None, max_length=80)
    phase_failures: list[Literal["setup", "call", "teardown"]] = Field(default_factory=list, max_length=3)
    output_truncated: bool = False


class RunnerSummary(StrictModel):
    total: int = Field(ge=0, le=MAX_CASES)
    passed: int = Field(ge=0, le=MAX_CASES)
    failed: int = Field(ge=0, le=MAX_CASES)
    errors: int = Field(ge=0, le=MAX_CASES)
    skipped: int = Field(ge=0, le=MAX_CASES)
    duration: float = Field(ge=0, allow_inf_nan=False)
    exit_code: int = Field(ge=0, le=5)


class RunnerPayload(StrictModel):
    protocol_version: Literal[2]
    collected: list[ExpectedCase] = Field(max_length=MAX_CASES)
    tests: list[RunnerTestEntry] = Field(max_length=MAX_CASES)
    summary: RunnerSummary
    completed: bool
    diagnostics: Diagnostics = Field(default_factory=Diagnostics)
    infrastructure_error: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def consistent(self) -> RunnerPayload:
        ids = [case.nodeid for case in self.collected]
        result_ids = [case.nodeid for case in self.tests]
        if len(ids) != len(set(ids)) or len(result_ids) != len(set(result_ids)):
            raise ValueError("Duplicate case IDs")
        for case in [*self.collected, *self.tests]:
            if len(case.markers) != len(set(case.markers)) or any(
                not marker.startswith("ag_") or len(marker) > 128 for marker in case.markers
            ):
                raise ValueError("Invalid marker mapping")
        if self.completed and (set(ids) != set(result_ids) or self.summary.exit_code not in (0, 1)):
            raise ValueError("Incomplete execution")
        collected = {case.nodeid: case for case in self.collected}
        for test in self.tests:
            case = collected.get(test.nodeid)
            if case is None or sorted(case.markers) != sorted(test.markers) or case.xfail != test.xfail:
                raise ValueError("Result membership mismatch")
            if test.outcome == "passed" and (test.phase_failures or test.output_truncated or test.xfail):
                raise ValueError("Invalid passing outcome")
        counts = {outcome: sum(test.outcome == outcome for test in self.tests)
                  for outcome in ("passed", "failed", "error", "skipped")}
        if (self.summary.total != len(self.tests) or self.summary.passed != counts["passed"]
                or self.summary.failed != counts["failed"] or self.summary.errors != counts["error"]
                or self.summary.skipped != counts["skipped"]):
            raise ValueError("Inconsistent summary")
        return self


class ValidatedManifest(StrictModel):
    protocol_version: Literal[2] = PROTOCOL_VERSION
    runtime_id: Literal["python-3.11.9-pytest-8.4.2-report-2"] = RUNTIME_ID
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    cases: list[ExpectedCase] = Field(min_length=1, max_length=MAX_CASES)

    @model_validator(mode="after")
    def unique(self) -> ValidatedManifest:
        if len({case.nodeid for case in self.cases}) != len(self.cases):
            raise ValueError("Duplicate manifest cases")
        return self

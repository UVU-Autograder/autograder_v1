from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from app.domains.runs.schemas import QueueBackpressure, RunCounters, RunState, RunStatusResponse

SESSION_TTL = timedelta(hours=1)


@dataclass
class SandboxRunRecord:
    run_id: str
    session_id: str
    course_id: str
    assignment_id: str
    state: RunState = "queue"
    status_reads: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(UTC) + SESSION_TTL
    )
    queue_position: int = 1
    warnings: int = 1
    max_score: int = 100
    celery_task_id: str | None = None



class UploadQuota(BaseModel):
    limit: int = Field(default=5, ge=1)
    window_seconds: int = Field(default=3600, ge=1)
    remaining: int = Field(ge=0)
    reset_at: str


class SandboxCourse(BaseModel):
    id: str
    title: str
    term: str
    sandbox_enabled_assignments: int = Field(ge=0)


class SandboxCourseListResponse(BaseModel):
    courses: list[SandboxCourse]


class SandboxAssignmentSummary(BaseModel):
    id: str
    course_id: str
    title: str
    sandbox_enabled: bool
    language: str
    max_score: int = Field(ge=0)
    upload_quota: UploadQuota
    module_name: str | None = None


class SandboxAssignmentListResponse(BaseModel):
    course_id: str
    assignments: list[SandboxAssignmentSummary]


class SandboxConstraint(BaseModel):
    label: str
    value: str


class SandboxRubricItem(BaseModel):
    key: str | None = None
    label: str
    points: int = Field(ge=0)
    extra_credit: bool = False
    pytest_marker: str | None = None
    item_type: Literal["pytest", "manual"] = "pytest"
    rubric_group_key: str | None = None
    inputs: list[str] | None = None
    outputs: list[str] | None = None


class SandboxRubricGroup(BaseModel):
    key: str
    label: str
    item_keys: list[str]


class SandboxAssignmentDetail(SandboxAssignmentSummary):
    description: str
    accepted_bundle_types: list[str]
    max_upload_bytes: int = Field(ge=1)
    constraints: list[SandboxConstraint]
    allowed_concepts: list[str] = Field(default_factory=list)
    rubric: list[SandboxRubricItem]
    rubric_groups: list[SandboxRubricGroup] = Field(default_factory=list)
    completion_requirements: list[dict] = Field(default_factory=list)


class FilePreviewMetadata(BaseModel):
    preview_available: bool
    preview_kind: Literal["metadata_only"]
    sanitized_entries: list[str]


class SandboxRunCreateResponse(BaseModel):
    run_id: str
    sandbox_session: str
    status_url: str
    result_url: str
    upload_quota: UploadQuota
    initial_status: RunStatusResponse
    file_preview: FilePreviewMetadata


class TestSummary(BaseModel):
    label: str
    status: Literal["passed", "failed", "warning", "not_run"]
    points_awarded: int = Field(ge=0)
    points_possible: int = Field(ge=0)
    message: str
    actual: str | None = None
    expected: str | None = None
    your_value: str | None = None
    expected_value: str | None = None
    expected_input: str | None = None
    group_key: str | None = None


class RubricGroupResultResponse(BaseModel):
    group_key: str
    label: str
    points_earned: int = Field(ge=0)
    points_possible: int = Field(ge=0)
    items: list[TestSummary] = Field(default_factory=list)


class SandboxWarning(BaseModel):
    code: str
    message: str


DEFAULT_RETENTION_NOTICE = "Sandbox results are session-only and are not retained as student submissions."


class SandboxRunResultResponse(BaseModel):
    run_id: str
    state: Literal["complete", "failure"]
    projected_score: int = Field(ge=0)
    max_score: int = Field(ge=0)
    warnings: list[SandboxWarning]
    test_summaries: list[TestSummary]
    rubric_groups: list[RubricGroupResultResponse] = Field(default_factory=list)
    sanitized_feedback: str
    file_preview: FilePreviewMetadata
    retention_notice: str = DEFAULT_RETENTION_NOTICE
    raw_output: str | None = None


class SandboxCancelResponse(BaseModel):
    run_id: str
    state: Literal["failure"]
    counters: RunCounters
    backpressure: QueueBackpressure
    message: str


class ConceptMetadata(BaseModel):
    key: str
    title: str
    syntax_patterns: list[str]
    nodes: list[str]


from typing import Literal

from pydantic import BaseModel, Field

from app.domains.runs.schemas import QueueBackpressure, RunCounters, RunStatusResponse


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
    due_label: str | None = None
    max_score: int = Field(ge=0)
    upload_quota: UploadQuota


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


class SandboxRubricGroup(BaseModel):
    key: str
    label: str
    item_keys: list[str]


class SandboxAssignmentDetail(SandboxAssignmentSummary):
    description: str
    accepted_bundle_types: list[str]
    max_upload_bytes: int = Field(ge=1)
    constraints: list[SandboxConstraint]
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


class SandboxWarning(BaseModel):
    code: str
    message: str


class SandboxRunResultResponse(BaseModel):
    run_id: str
    state: Literal["complete", "failure"]
    projected_score: int = Field(ge=0)
    max_score: int = Field(ge=0)
    warnings: list[SandboxWarning]
    test_summaries: list[TestSummary]
    sanitized_feedback: str
    file_preview: FilePreviewMetadata
    retention_notice: str


class SandboxCancelResponse(BaseModel):
    run_id: str
    state: Literal["failure"]
    counters: RunCounters
    backpressure: QueueBackpressure
    message: str

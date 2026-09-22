from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RunState = Literal["queue", "run", "complete", "failure"]
EtaBand = Literal["under_1_min", "1_to_3_min", "3_to_5_min", "over_5_min"]


class RunCounters(BaseModel):
    total: int = Field(ge=0)
    queued: int = Field(ge=0)
    running: int = Field(ge=0)
    completed: int = Field(ge=0)
    failed: int = Field(ge=0)
    warnings: int = Field(ge=0)


class QueueBackpressure(BaseModel):
    high_load_threshold: int = Field(default=40, ge=1)
    full_queue_threshold: int = Field(default=50, ge=1)
    current_waiting: int = Field(ge=0)
    high_load: bool
    accepting_runs: bool


class RunStatusResponse(BaseModel):
    run_id: str
    state: RunState
    queue_position: int | None = Field(default=None, ge=1)
    eta_band: EtaBand | None = None
    counters: RunCounters
    backpressure: QueueBackpressure
    message: str | None = None


from datetime import datetime


class RunSummaryResponse(BaseModel):
    id: int
    workflow_type: str
    actor_user_id: int | None = None
    assignment_id: int
    section_id: int | None = None
    status: str
    total_submission_count: int
    success_count: int
    warning_count: int
    failure_count: int
    timeout_count: int
    failure_summary: dict
    created_at: datetime

    review_expires_at: datetime | None = None
    deletion_deadline_at: datetime | None = None
    retention_state: Literal["available", "cleanup_pending", "cleanup_failed", "deleted"] = "available"
    cleanup_reason: str | None = None
    cleanup_last_attempt_at: datetime | None = None
    deleted_at: datetime | None = None
    cleanup_failure_category: str | None = None

    @field_validator("created_at", "review_expires_at", "deletion_deadline_at", "cleanup_last_attempt_at", "deleted_at")
    @classmethod
    def utc_dates(cls, value: datetime | None) -> datetime | None:
        from datetime import UTC

        return value.replace(tzinfo=UTC) if value is not None and value.tzinfo is None else value

    model_config = ConfigDict(from_attributes=True)


class RunSummaryListResponse(BaseModel):
    runs: list[RunSummaryResponse]


class ManualGradeInput(BaseModel):
    score: int | None = Field(default=None, ge=0, strict=True)
    comments: str | None = Field(default="")


class UpdateManualGradesRequest(BaseModel):
    grades: dict[str, ManualGradeInput]
    overall_comment: str | None = None


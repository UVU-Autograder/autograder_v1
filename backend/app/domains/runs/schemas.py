from typing import Literal

from pydantic import BaseModel, Field

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

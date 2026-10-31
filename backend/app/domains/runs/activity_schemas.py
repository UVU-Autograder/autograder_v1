"""Pydantic schemas for student sandbox activity, practice engagement, and bottleneck telemetry."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ActivityTimeseriesPoint(BaseModel):
    """Aggregate activity telemetry bucket over an hourly or daily interval."""

    timestamp: str = Field(description="ISO 8601 interval start timestamp")
    run_count: int = Field(default=0, description="Total sandbox submissions in interval")
    active_sessions: int = Field(default=0, description="Unique student sessions active in interval")
    success_count: int = Field(default=0, description="Passing runs")
    failure_count: int = Field(default=0, description="Failing runs")


class AttemptBucket(BaseModel):
    """Distribution bucket for student attempt counts prior to passing or stopping."""

    bucket_label: str = Field(description="Display label (e.g. '1 attempt', '2-3 attempts')")
    session_count: int = Field(default=0, description="Number of distinct student sessions in this bucket")
    percentage: float = Field(default=0.0, description="Percentage of total active sessions")


class BottleneckItem(BaseModel):
    """Frequent test failure marker, syntax error, or concept violation."""

    key: str = Field(description="Identifier or test marker name")
    category: str = Field(description="Error category (e.g. 'assertion', 'syntax', 'concept', 'timeout')")
    count: int = Field(default=0, description="Frequency of occurrence")
    description: str | None = Field(default=None, description="Human-readable description or hint")


class AssignmentActivitySummary(BaseModel):
    """Activity and engagement summary for a single course assignment."""

    assignment_id: int = Field(description="Relational assignment ID")
    assignment_code: str = Field(description="Assignment key (e.g. 'lab1', 'ds1')")
    title: str = Field(description="Assignment title")
    total_runs: int = Field(default=0, description="Total student runs")
    active_students: int = Field(default=0, description="Unique student sessions")
    pass_rate: float = Field(default=0.0, description="Percentage of runs with passing outcome (0-100)")
    top_bottleneck: str | None = Field(default=None, description="Most frequent failure key or category")


class SystemActivityResponse(BaseModel):
    """System-wide operational and pedagogical activity telemetry for staff administrators."""

    window_hours: int = Field(description="Analysis time window in hours")
    total_sandbox_runs: int = Field(default=0, description="Total sandbox executions in window")
    active_student_sessions: int = Field(default=0, description="Unique hashed student sessions in window")
    overall_pass_rate: float = Field(default=0.0, description="Overall sandbox pass percentage (0-100)")
    total_ai_tokens: int = Field(default=0, description="Total AI tokens consumed by sandbox requests")
    total_ai_requests: int = Field(default=0, description="Total AI coaching prompts requested")
    velocity: list[ActivityTimeseriesPoint] = Field(default_factory=list, description="Hourly activity velocity")
    attempt_distribution: list[AttemptBucket] = Field(default_factory=list, description="Student attempt histogram")
    top_bottlenecks: list[BottleneckItem] = Field(default_factory=list, description="Top failure bottlenecks")
    assignments: list[AssignmentActivitySummary] = Field(default_factory=list, description="Breakdown by assignment")


class CourseActivityResponse(BaseModel):
    """Course-scoped student engagement telemetry for instructors and teaching assistants."""

    course_id: int = Field(description="Relational course ID")
    course_code: str = Field(description="Course code (e.g. 'cs1410')")
    course_title: str = Field(description="Course title")
    window_hours: int = Field(description="Analysis time window in hours")
    total_sandbox_runs: int = Field(default=0, description="Total sandbox executions for course")
    active_student_sessions: int = Field(default=0, description="Unique hashed student sessions for course")
    overall_pass_rate: float = Field(default=0.0, description="Course sandbox pass percentage (0-100)")
    total_ai_tokens: int = Field(default=0, description="Total AI tokens consumed for course assignments")
    total_ai_requests: int = Field(default=0, description="Total AI coaching prompts for course assignments")
    velocity: list[ActivityTimeseriesPoint] = Field(default_factory=list, description="Hourly activity velocity")
    attempt_distribution: list[AttemptBucket] = Field(default_factory=list, description="Student attempt histogram")
    top_bottlenecks: list[BottleneckItem] = Field(default_factory=list, description="Top failure bottlenecks")
    assignments: list[AssignmentActivitySummary] = Field(default_factory=list, description="Breakdown by assignment")

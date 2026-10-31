"""Domain service for aggregating student sandbox activity, practice engagement, and bottleneck telemetry."""
from __future__ import annotations

import hashlib
import logging
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.assignments.models import Assignment
from app.domains.courses.models import Course
from app.domains.runs.activity_schemas import (
    ActivityTimeseriesPoint,
    AssignmentActivitySummary,
    AttemptBucket,
    BottleneckItem,
    CourseActivityResponse,
    SystemActivityResponse,
)
from app.domains.runs.models import RunSummary

logger = logging.getLogger(__name__)


def record_sandbox_telemetry(
    *,
    assignment_id: int | None,
    session_id: str | None,
    status: str,
    failure_category: str | None = None,
    failure_summary: dict[str, Any] | None = None,
    token_usage_metadata: dict[str, Any] | None = None,
    grade_seconds: float | None = None,
) -> None:
    """Non-blocking, fail-safe database persistence of aggregate sandbox run telemetry (FERPA compliant)."""
    if not assignment_id:
        return

    try:
        from app.db.session import SessionLocal

        session_hash = None
        if session_id:
            session_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()

        summary_payload = dict(failure_summary or {})
        if failure_category and "failure_category" not in summary_payload:
            summary_payload["failure_category"] = failure_category

        with SessionLocal() as db:
            run_sum = RunSummary(
                workflow_type="sandbox",
                assignment_id=assignment_id,
                sandbox_session_hash=session_hash,
                status=status,
                total_submission_count=1,
                success_count=1 if status == "complete" else 0,
                failure_count=1 if status == "failure" else 0,
                failure_summary=summary_payload,
                token_usage_metadata=token_usage_metadata or {},
                export_packaging_seconds=grade_seconds,
            )
            db.add(run_sum)
            db.commit()
    except Exception as exc:
        logger.debug("Non-blocking failure to persist sandbox run telemetry: %s", exc)


def record_sandbox_ai_telemetry(
    *,
    assignment_id: int | None,
    session_id: str | None,
    token_usage: dict[str, Any],
) -> None:
    """Non-blocking record of AI coaching token usage for an assignment."""
    if not assignment_id or not token_usage:
        return

    try:
        from app.db.session import SessionLocal

        session_hash = None
        if session_id:
            session_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()

        with SessionLocal() as db:
            run_sum = RunSummary(
                workflow_type="sandbox_ai",
                assignment_id=assignment_id,
                sandbox_session_hash=session_hash,
                status="complete",
                total_submission_count=0,
                success_count=0,
                failure_count=0,
                token_usage_metadata=token_usage,
            )
            db.add(run_sum)
            db.commit()
    except Exception as exc:
        logger.debug("Non-blocking failure to record sandbox AI telemetry: %s", exc)


def _build_attempt_distribution(session_attempts: dict[str, int]) -> list[AttemptBucket]:
    """Calculate bucketed attempt distribution histogram from per-session attempt counts."""
    if not session_attempts:
        return [
            AttemptBucket(bucket_label="1 attempt", session_count=0, percentage=0.0),
            AttemptBucket(bucket_label="2-3 attempts", session_count=0, percentage=0.0),
            AttemptBucket(bucket_label="4-6 attempts", session_count=0, percentage=0.0),
            AttemptBucket(bucket_label="7-10 attempts", session_count=0, percentage=0.0),
            AttemptBucket(bucket_label=">10 attempts", session_count=0, percentage=0.0),
        ]

    total_sessions = len(session_attempts)
    counts = {
        "1 attempt": 0,
        "2-3 attempts": 0,
        "4-6 attempts": 0,
        "7-10 attempts": 0,
        ">10 attempts": 0,
    }

    for attempts in session_attempts.values():
        if attempts == 1:
            counts["1 attempt"] += 1
        elif 2 <= attempts <= 3:
            counts["2-3 attempts"] += 1
        elif 4 <= attempts <= 6:
            counts["4-6 attempts"] += 1
        elif 7 <= attempts <= 10:
            counts["7-10 attempts"] += 1
        else:
            counts[">10 attempts"] += 1

    return [
        AttemptBucket(
            bucket_label=label,
            session_count=count,
            percentage=round((count / total_sessions) * 100, 1),
        )
        for label, count in counts.items()
    ]


def _build_velocity_timeseries(
    runs: list[RunSummary],
    window_start: datetime,
    window_hours: int,
) -> list[ActivityTimeseriesPoint]:
    """Bucket sandbox runs into hourly or daily time slices."""
    # Determine bucket size in hours
    if window_hours <= 48:
        step_hours = 2
        num_buckets = window_hours // step_hours
    elif window_hours <= 168:
        step_hours = 6
        num_buckets = window_hours // step_hours
    else:
        step_hours = 24
        num_buckets = max(1, window_hours // step_hours)

    buckets: list[dict[str, Any]] = []
    bucket_interval = timedelta(hours=step_hours)

    for i in range(num_buckets):
        b_start = window_start + (i * bucket_interval)
        b_end = b_start + bucket_interval
        buckets.append({
            "start": b_start,
            "end": b_end,
            "timestamp": b_start.isoformat(),
            "runs": 0,
            "success": 0,
            "failure": 0,
            "sessions": set(),
        })

    for run in runs:
        if run.created_at is None:
            continue
        run_dt = run.created_at if run.created_at.tzinfo else run.created_at.replace(tzinfo=UTC)
        for b in buckets:
            if b["start"] <= run_dt < b["end"]:
                b["runs"] += 1
                if run.status == "complete":
                    b["success"] += 1
                else:
                    b["failure"] += 1
                if run.sandbox_session_hash:
                    b["sessions"].add(run.sandbox_session_hash)
                break

    return [
        ActivityTimeseriesPoint(
            timestamp=b["timestamp"],
            run_count=b["runs"],
            active_sessions=len(b["sessions"]),
            success_count=b["success"],
            failure_count=b["failure"],
        )
        for b in buckets
    ]


def _extract_bottlenecks(runs: list[RunSummary], limit: int = 8) -> list[BottleneckItem]:
    """Rank the most frequent failure markers and categories across failed runs."""
    counter: Counter[tuple[str, str]] = Counter()

    for run in runs:
        if run.status != "failure" or not run.failure_summary:
            continue
        fs = run.failure_summary
        if not isinstance(fs, dict):
            continue

        category = fs.get("failure_category", "assertion")

        # Extract failed test markers or items if present
        failed_items = fs.get("failed_items") or fs.get("failed_keys")
        if isinstance(failed_items, list) and failed_items:
            for item in failed_items:
                if isinstance(item, str):
                    counter[(item, "assertion")] += 1
                elif isinstance(item, dict) and "key" in item:
                    counter[(item["key"], "assertion")] += 1
        else:
            category_label = str(category).replace("_", " ").title()
            counter[(category_label, category)] += 1

    bottlenecks: list[BottleneckItem] = []
    for (key, cat), count in counter.most_common(limit):
        desc = None
        if cat == "syntax_error":
            desc = "Syntax or parse error before test execution"
        elif cat == "concept_blocked":
            desc = "Disallowed construct or forbidden library usage"
        elif cat == "timeout":
            desc = "Execution exceeded bounded time limit"
        bottlenecks.append(BottleneckItem(key=key, category=cat, count=count, description=desc))

    return bottlenecks


def get_system_activity_summary(
    db: Session,
    window_hours: int = 168,
) -> SystemActivityResponse:
    """Compute aggregate system-wide student activity telemetry across all courses."""
    window_hours = max(1, min(window_hours, 8760))
    window_start = datetime.now(UTC) - timedelta(hours=window_hours)

    runs = list(
        db.scalars(
            select(RunSummary)
            .where(
                RunSummary.workflow_type.in_(("sandbox", "sandbox_ai")),
                RunSummary.created_at >= window_start,
            )
            .order_by(RunSummary.created_at.asc())
        )
    )

    sandbox_runs = [r for r in runs if r.workflow_type == "sandbox"]
    ai_runs = [r for r in runs if r.workflow_type == "sandbox_ai"]

    total_sandbox_runs = len(sandbox_runs)
    session_attempts: dict[str, int] = defaultdict(int)
    success_count = 0
    total_tokens = 0

    for r in runs:
        if r.token_usage_metadata and isinstance(r.token_usage_metadata, dict):
            total_tokens += r.token_usage_metadata.get("total_tokens", 0)

    for r in sandbox_runs:
        if r.sandbox_session_hash:
            session_attempts[r.sandbox_session_hash] += 1
        if r.status == "complete":
            success_count += 1

    active_sessions = len(session_attempts)
    pass_rate = round((success_count / total_sandbox_runs) * 100, 1) if total_sandbox_runs > 0 else 0.0

    velocity = _build_velocity_timeseries(sandbox_runs, window_start, window_hours)
    attempt_distribution = _build_attempt_distribution(session_attempts)
    top_bottlenecks = _extract_bottlenecks(sandbox_runs)

    # Per-assignment summary
    assignment_runs: dict[int, list[RunSummary]] = defaultdict(list)
    for r in sandbox_runs:
        assignment_runs[r.assignment_id].append(r)

    assignments_summary: list[AssignmentActivitySummary] = []
    if assignment_runs:
        db_assignments = {
            a.id: a
            for a in db.scalars(
                select(Assignment).where(Assignment.id.in_(assignment_runs.keys()))
            )
        }
        for aid, a_runs in assignment_runs.items():
            db_a = db_assignments.get(aid)
            if not db_a:
                continue
            a_success = sum(1 for r in a_runs if r.status == "complete")
            a_sessions = {r.sandbox_session_hash for r in a_runs if r.sandbox_session_hash}
            a_bottlenecks = _extract_bottlenecks(a_runs, limit=1)
            top_bn = a_bottlenecks[0].key if a_bottlenecks else None

            assignments_summary.append(
                AssignmentActivitySummary(
                    assignment_id=db_a.id,
                    assignment_code=db_a.slug,
                    title=db_a.title,
                    total_runs=len(a_runs),
                    active_students=len(a_sessions),
                    pass_rate=round((a_success / len(a_runs)) * 100, 1) if a_runs else 0.0,
                    top_bottleneck=top_bn,
                )
            )
        assignments_summary.sort(key=lambda a: a.total_runs, reverse=True)

    return SystemActivityResponse(
        window_hours=window_hours,
        total_sandbox_runs=total_sandbox_runs,
        active_student_sessions=active_sessions,
        overall_pass_rate=pass_rate,
        total_ai_tokens=total_tokens,
        total_ai_requests=len(ai_runs),
        velocity=velocity,
        attempt_distribution=attempt_distribution,
        top_bottlenecks=top_bottlenecks,
        assignments=assignments_summary,
    )


def get_course_activity_summary(
    db: Session,
    course_code: str,
    window_hours: int = 168,
) -> CourseActivityResponse | None:
    """Compute course-scoped student activity telemetry for instructors."""
    window_hours = max(1, min(window_hours, 8760))
    course = db.scalar(select(Course).where(Course.code == course_code))
    if not course:
        return None

    course_assignments = list(db.scalars(select(Assignment).where(Assignment.course_id == course.id)))
    assignment_ids = [a.id for a in course_assignments]

    if not assignment_ids:
        return CourseActivityResponse(
            course_id=course.id,
            course_code=course.code,
            course_title=course.title,
            window_hours=window_hours,
            total_sandbox_runs=0,
            active_student_sessions=0,
            overall_pass_rate=0.0,
            total_ai_tokens=0,
            total_ai_requests=0,
            velocity=[],
            attempt_distribution=_build_attempt_distribution({}),
            top_bottlenecks=[],
            assignments=[],
        )

    window_start = datetime.now(UTC) - timedelta(hours=window_hours)

    runs = list(
        db.scalars(
            select(RunSummary)
            .where(
                RunSummary.assignment_id.in_(assignment_ids),
                RunSummary.workflow_type.in_(("sandbox", "sandbox_ai")),
                RunSummary.created_at >= window_start,
            )
            .order_by(RunSummary.created_at.asc())
        )
    )

    sandbox_runs = [r for r in runs if r.workflow_type == "sandbox"]
    ai_runs = [r for r in runs if r.workflow_type == "sandbox_ai"]

    total_sandbox_runs = len(sandbox_runs)
    session_attempts: dict[str, int] = defaultdict(int)
    success_count = 0
    total_tokens = 0

    for r in runs:
        if r.token_usage_metadata and isinstance(r.token_usage_metadata, dict):
            total_tokens += r.token_usage_metadata.get("total_tokens", 0)

    for r in sandbox_runs:
        if r.sandbox_session_hash:
            session_attempts[r.sandbox_session_hash] += 1
        if r.status == "complete":
            success_count += 1

    active_sessions = len(session_attempts)
    pass_rate = round((success_count / total_sandbox_runs) * 100, 1) if total_sandbox_runs > 0 else 0.0

    velocity = _build_velocity_timeseries(sandbox_runs, window_start, window_hours)
    attempt_distribution = _build_attempt_distribution(session_attempts)
    top_bottlenecks = _extract_bottlenecks(sandbox_runs)

    assignment_runs: dict[int, list[RunSummary]] = defaultdict(list)
    for r in sandbox_runs:
        assignment_runs[r.assignment_id].append(r)

    assignments_summary: list[AssignmentActivitySummary] = []
    for a in course_assignments:
        a_runs = assignment_runs.get(a.id, [])
        a_success = sum(1 for r in a_runs if r.status == "complete")
        a_sessions = {r.sandbox_session_hash for r in a_runs if r.sandbox_session_hash}
        a_bottlenecks = _extract_bottlenecks(a_runs, limit=1)
        top_bn = a_bottlenecks[0].key if a_bottlenecks else None

        assignments_summary.append(
            AssignmentActivitySummary(
                assignment_id=a.id,
                assignment_code=a.slug,
                title=a.title,
                total_runs=len(a_runs),
                active_students=len(a_sessions),
                pass_rate=round((a_success / len(a_runs)) * 100, 1) if a_runs else 0.0,
                top_bottleneck=top_bn,
            )
        )
    assignments_summary.sort(key=lambda a: a.total_runs, reverse=True)

    return CourseActivityResponse(
        course_id=course.id,
        course_code=course.code,
        course_title=course.title,
        window_hours=window_hours,
        total_sandbox_runs=total_sandbox_runs,
        active_student_sessions=active_sessions,
        overall_pass_rate=pass_rate,
        total_ai_tokens=total_tokens,
        total_ai_requests=len(ai_runs),
        velocity=velocity,
        attempt_distribution=attempt_distribution,
        top_bottlenecks=top_bottlenecks,
        assignments=assignments_summary,
    )

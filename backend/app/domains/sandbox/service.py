from __future__ import annotations

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from app.core.settings import get_settings
from app.domains.runs.queue_admission import (
    QueueFullError,
    backpressure_snapshot,
    eta_band_for_position,
    release_execution_slots,
    reserve_execution_slots,
    waiting_count,
)
from app.domains.runs.schemas import (
    QueueBackpressure,
    RunCounters,
    RunState,
    RunStatusResponse,
)
from app.domains.sandbox.schemas import (
    FilePreviewMetadata,
    RubricGroupResultResponse,
    SandboxCancelResponse,
    SandboxRunCreateResponse,
    SandboxRunRecord,
    SandboxRunResultResponse,
    SandboxWarning,
    TestSummary,
    UploadQuota,
)

from app.domains.sandbox.store import (
    InMemoryRunStateStore,
    RedisRunStateStore,
    RunStateStore,
)

SESSION_TTL = timedelta(hours=1)


class SandboxService:

    """Deep domain service for student sandbox runs, quota tracking, and status monitoring.

    Persistence and rate-limiting operations are delegated to a RunStateStore instance.
    """

    def __init__(
        self,
        use_celery: bool = False,
        store: RunStateStore | None = None,
    ) -> None:
        self._use_celery = use_celery
        if store is not None:
            self._store = store
        elif use_celery:
            self._store = RedisRunStateStore()
        else:
            self._store = InMemoryRunStateStore()

    @property
    def _runs(self) -> dict[str, SandboxRunRecord]:
        if isinstance(self._store, InMemoryRunStateStore):
            return self._store._runs
        return {}

    @property
    def _session_uploads(self) -> dict[str, list[datetime]]:
        if isinstance(self._store, InMemoryRunStateStore):
            return self._store._session_uploads
        return {}

    @property
    def _upload_limit(self) -> int:

        return get_settings().sandbox_upload_limit

    @property
    def _upload_window(self) -> timedelta:
        return timedelta(seconds=get_settings().sandbox_upload_window_seconds)

    def quota_for_session(self, session_id: str | None) -> UploadQuota:
        return self._store.get_quota(session_id, self._upload_limit, self._upload_window)

    def create_run(
        self,
        course_id: str,
        assignment_id: str,
        session_id: str | None,
        assignment_exists: bool | None = None,
        max_score: int = 100,
        zip_data: bytes | None = None,
        config_json: dict | None = None,
        artifact_refs: dict[str, str] | None = None,
        allowed_concepts: list[str] | None = None,
        stdin: str | None = None,
    ) -> tuple[SandboxRunCreateResponse | None, str, int | None]:
        """Create a sandbox run record and optionally dispatch a Celery task with optional stdin."""
        if not assignment_exists:
            return None, session_id or self._new_session(), None

        session = session_id or self._new_session()
        quota = self.quota_for_session(session)
        if quota.remaining <= 0:
            return None, session, 429

        try:
            waiting = reserve_execution_slots(1)
        except QueueFullError:
            return None, session, 503

        now = datetime.now(UTC)
        self._store.record_upload(session, now)

        run_id = f"run_{token_urlsafe(16)}"
        record = SandboxRunRecord(
            run_id=run_id,
            session_id=session,
            course_id=course_id,
            assignment_id=assignment_id,
            queue_position=max(1, waiting),
            max_score=max_score,
        )
        self._store.save_run(record)


        # Dispatch Celery task if enabled and ZIP data is provided
        if self._use_celery and zip_data is not None and config_json is not None:
            import base64

            from app.domains.runs.tasks import grade_sandbox_run, set_run_state

            zip_b64 = base64.b64encode(zip_data).decode("ascii")
            try:
                set_run_state(
                    run_id,
                    "queue",
                    {
                        "queue_position": record.queue_position,
                        "eta_band": eta_band_for_position(record.queue_position),
                    },
                )
            except Exception:
                pass
            grade_result = grade_sandbox_run.delay(
                run_id=run_id,
                zip_data_b64=zip_b64,
                config_json=config_json,
                artifact_refs=artifact_refs or {},
                allowed_concepts=allowed_concepts or [],
                stdin=stdin,
            )
            record.celery_task_id = grade_result.id

        status = self._status_for(record)
        return (
            SandboxRunCreateResponse(
                run_id=run_id,
                sandbox_session=session,
                status_url=f"/runs/{run_id}/status",
                result_url=f"/sandbox/runs/{run_id}/result",
                upload_quota=self._quota_for(session),
                initial_status=status,
                file_preview=self._file_preview(),
            ),
            session,
            None,
        )

    def get_status(self, run_id: str) -> RunStatusResponse | None:
        self._expire_old_runs()

        # Try Redis first if Celery mode is active
        if self._use_celery:
            try:
                from app.domains.runs.tasks import get_run_state
                redis_state = get_run_state(run_id)
                if redis_state is not None:
                    state = redis_state.get("state", "queue")
                    queue_pos = redis_state.get("queue_position")
                    return RunStatusResponse(
                        run_id=run_id,
                        state=state,
                        queue_position=queue_pos if state == "queue" else None,
                        eta_band=eta_band_for_position(queue_pos)
                        if state == "queue"
                        else None,
                        counters=self._counters(),
                        backpressure=self._backpressure(),
                        message=self._message_for(state),
                    )
            except Exception:
                pass

        # Fall back to store
        record = self._store.get_run(run_id)
        if record is None:
            return None
        status = self._status_for(record)
        self._advance(record)
        return status

    def cancel_run(
        self, run_id: str, session_id: str | None
    ) -> SandboxCancelResponse | str | None:
        self._expire_old_runs()
        record = self._store.get_run(run_id)
        if record is None or record.session_id != session_id:
            return None
        if record.state != "queue":
            return "not_cancelable"

        if self._use_celery:
            try:
                from app.domains.runs.tasks import get_run_state

                redis_state = get_run_state(run_id)
                if redis_state and redis_state.get("state") not in (None, "queue"):
                    return "not_cancelable"
            except Exception:
                pass

        record.state = "failure"

        try:
            if self._use_celery:
                try:
                    from app.domains.runs.tasks import mark_run_cancelled, set_run_state
                    from app.integrations.celery.app import celery_app

                    mark_run_cancelled(run_id)
                    set_run_state(run_id, "failure", {"failure_category": "cancelled"})
                    if record.celery_task_id:
                        celery_app.control.revoke(record.celery_task_id, terminate=False)
                except Exception:
                    pass
        finally:
            release_execution_slots(1)

        return SandboxCancelResponse(
            run_id=run_id,
            state="failure",
            counters=self._counters(),
            backpressure=self._backpressure(),
            message="Queued sandbox run cancelled before execution started.",
        )

    def get_result(
        self, run_id: str, session_id: str | None
    ) -> SandboxRunResultResponse | str | None:
        self._expire_old_runs()
        record = self._store.get_run(run_id)
        if record is None or record.session_id != session_id:
            return None


        # Try Redis for real results if in Celery mode
        if self._use_celery:
            try:
                from app.domains.runs.tasks import get_run_result, get_run_state
                redis_state = get_run_state(run_id)
                if redis_state is None:
                    return "not_ready"
                state = redis_state.get("state", "queue")
                if state not in {"complete", "failure"}:
                    return "not_ready"

                redis_result = get_run_result(run_id)
                if redis_result is None:
                    return "not_ready"

                if state == "failure":
                    return SandboxRunResultResponse(
                        run_id=run_id,
                        state="failure",
                        projected_score=0,
                        max_score=record.max_score,
                        warnings=[
                            SandboxWarning(
                                code=redis_result.get("failure_category", "internal_error"),
                                message=redis_result.get("failure_message", "Run failed."),
                            )
                        ],
                        test_summaries=[],
                        sanitized_feedback="The sandbox run ended with an error.",
                        file_preview=self._file_preview(),
                    )

                # Build test summaries from real results
                test_summaries = []
                for tr in redis_result.get("test_results", []):
                    failed_sub = None
                    actual_val = None
                    expected_val = None
                    expected_input_val = None

                    for sub in tr.get("test_results", []):
                        if sub.get("actual") is not None and actual_val is None:
                            actual_val = sub.get("actual")
                        if sub.get("expected") is not None and expected_val is None:
                            expected_val = sub.get("expected")
                        if sub.get("expected_input") is not None and expected_input_val is None:
                            expected_input_val = sub.get("expected_input")
                        if sub.get("outcome") != "passed":
                            failed_sub = sub
                            break

                    msg = tr.get("label", "")
                    if failed_sub:
                        msg = failed_sub.get("message") or ""
                        if failed_sub.get("actual") is not None:
                            actual_val = failed_sub.get("actual")
                        if failed_sub.get("expected") is not None:
                            expected_val = failed_sub.get("expected")
                        if failed_sub.get("expected_input") is not None:
                            expected_input_val = failed_sub.get("expected_input")

                    your_val = tr.get("your_value") or actual_val
                    exp_val = tr.get("expected_value") or expected_val

                    test_summaries.append(
                        TestSummary(
                            label=tr.get("label", tr.get("key", "Unknown")),
                            status="passed" if tr.get("passed") else "failed",
                            points_awarded=tr.get("points_awarded", 0),
                            points_possible=tr.get("points", 0),
                            message=msg,
                            actual=actual_val,
                            expected=expected_val,
                            your_value=your_val,
                            expected_value=exp_val,
                            expected_input=expected_input_val,
                        )
                    )

                warnings = [
                    SandboxWarning(code=w.get("code", "warning"), message=w.get("message", ""))
                    for w in redis_result.get("warnings", [])
                ]

                # Group test summaries into rubric groups if available
                rubric_groups = []
                default_group = RubricGroupResultResponse(
                    group_key="default",
                    label="Autograded Tests",
                    points_earned=sum(ts.points_awarded for ts in test_summaries),
                    points_possible=sum(ts.points_possible for ts in test_summaries),
                    items=test_summaries,
                )
                if test_summaries:
                    rubric_groups.append(default_group)

                return SandboxRunResultResponse(
                    run_id=run_id,
                    state="complete",
                    projected_score=redis_result.get("score", 0),
                    max_score=redis_result.get("max_score", record.max_score),
                    warnings=warnings,
                    test_summaries=test_summaries,
                    rubric_groups=rubric_groups,
                    sanitized_feedback="Review your results above.",
                    file_preview=self._file_preview(),
                    raw_output=redis_result.get("raw_output"),
                )
            except Exception:
                pass

        # In-memory mock behavior for contract tests
        if record.state not in {"complete", "failure"}:
            return "not_ready"
        if record.state == "failure":
            return SandboxRunResultResponse(
                run_id=run_id,
                state="failure",
                projected_score=0,
                max_score=self._assignment_max_score(record),
                warnings=[
                    SandboxWarning(code="cancelled", message="Run did not execute.")
                ],
                test_summaries=[],
                sanitized_feedback="The sandbox run ended before projected grading completed.",
                file_preview=self._file_preview(),
            )
        return SandboxRunResultResponse(
            run_id=run_id,
            state="complete",
            projected_score=86,
            max_score=100,
            warnings=[
                SandboxWarning(
                    code="style_signal",
                    message="One style check reported a non-blocking improvement.",
                )
            ],
            test_summaries=[
                TestSummary(
                    label="Public behavior checks",
                    status="passed",
                    points_awarded=60,
                    points_possible=60,
                    message="Visible examples matched expected behavior.",
                ),
                TestSummary(
                    label="Edge-case checks",
                    status="warning",
                    points_awarded=26,
                    points_possible=40,
                    message="Some boundary behavior may need review.",
                ),
            ],
            sanitized_feedback=(
                "Your projected result is strong. Review boundary-case handling and keep "
                "the implementation organized before an official submission."
            ),
            file_preview=self._file_preview(),
        )

    def _redis_conn(self):
        import redis
        return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)

    def _quota_for(self, session_id: str | None) -> UploadQuota:
        now = datetime.now(UTC)
        if session_id is None:
            return UploadQuota(
                limit=self._upload_limit,
                window_seconds=int(self._upload_window.total_seconds()),
                remaining=self._upload_limit,
                reset_at=(now + self._upload_window).isoformat(),
            )

        def _fallback_quota():
            uploads = [
                ts
                for ts in self._session_uploads.get(session_id, [])
                if now - ts < self._upload_window
            ]
            self._session_uploads[session_id] = uploads
            reset_at = now + self._upload_window
            if uploads:
                reset_at = uploads[0] + self._upload_window
            return UploadQuota(
                limit=self._upload_limit,
                window_seconds=int(self._upload_window.total_seconds()),
                remaining=max(self._upload_limit - len(uploads), 0),
                reset_at=reset_at.isoformat(),
            )

        if not self._use_celery:
            return _fallback_quota()

        try:
            # Redis rate-limiting
            r = self._redis_conn()
            key = f"sandbox:uploads:{session_id}"
            raw_uploads = r.lrange(key, 0, -1)
            uploads_ts = []
            for raw in raw_uploads:
                try:
                    uploads_ts.append(float(raw))
                except ValueError:
                    pass

            now_ts = now.timestamp()
            cutoff_ts = now_ts - self._upload_window.total_seconds()
            active_ts = [ts for ts in uploads_ts if ts > cutoff_ts]

            r.delete(key)
            if active_ts:
                r.rpush(key, *[str(ts) for ts in active_ts])
                r.expire(key, int(self._upload_window.total_seconds()))

            remaining = max(self._upload_limit - len(active_ts), 0)
            if active_ts:
                oldest_dt = datetime.fromtimestamp(min(active_ts), tz=UTC)
                reset_at = oldest_dt + self._upload_window
            else:
                reset_at = now + self._upload_window

            return UploadQuota(
                limit=self._upload_limit,
                window_seconds=int(self._upload_window.total_seconds()),
                remaining=remaining,
                reset_at=reset_at.isoformat(),
            )
        except Exception:
            return _fallback_quota()

    def _status_for(self, record: SandboxRunRecord) -> RunStatusResponse:
        return RunStatusResponse(
            run_id=record.run_id,
            state=record.state,
            queue_position=record.queue_position if record.state == "queue" else None,
            eta_band=eta_band_for_position(record.queue_position)
            if record.state == "queue"
            else None,
            counters=self._counters(),
            backpressure=self._backpressure(),
            message=self._message_for(record.state),
        )

    def _advance(self, record: SandboxRunRecord) -> None:
        previous = record.state
        record.status_reads += 1
        if record.state == "queue" and record.status_reads >= 1:
            record.state = "run"
        elif record.state == "run" and record.status_reads >= 2:
            record.state = "complete"
        if previous not in {"complete", "failure"} and record.state in {
            "complete",
            "failure",
        }:
            release_execution_slots(1)

    def _message_for(self, state: RunState) -> str:
        return {
            "queue": "Sandbox run accepted and waiting for execution capacity.",
            "run": "Sandbox run is executing in the mock contract prototype.",
            "complete": "Sandbox run completed. Fetch session-only projected feedback from the sandbox result endpoint.",
            "failure": "Sandbox run ended with a coarse failure state.",
        }[state]

    def _counters(self) -> RunCounters:
        values = self._store.list_runs()
        if self._use_celery:
            try:
                from app.domains.runs.tasks import get_run_state
                for item in values:
                    redis_state = get_run_state(item.run_id)
                    if redis_state:
                        item.state = redis_state.get("state", "queue")
            except Exception:
                pass
        return RunCounters(
            total=len(values),
            queued=sum(1 for item in values if item.state == "queue"),
            running=sum(1 for item in values if item.state == "run"),
            completed=sum(1 for item in values if item.state == "complete"),
            failed=sum(1 for item in values if item.state == "failure"),
            warnings=sum(item.warnings for item in values if item.state == "complete"),
        )

    def _backpressure(self) -> QueueBackpressure:
        return backpressure_snapshot()

    def _queued_count(self) -> int:
        return waiting_count()

    def _assignment_max_score(self, record: SandboxRunRecord) -> int:
        return record.max_score

    def _file_preview(self) -> FilePreviewMetadata:
        return FilePreviewMetadata(
            preview_available=False,
            preview_kind="metadata_only",
            sanitized_entries=["submission_bundle", "source_file_1", "support_file_1"],
        )

    def _new_session(self) -> str:
        return f"sandbox_{token_urlsafe(18)}"

    def _expire_old_runs(self) -> None:
        now = datetime.now(UTC)
        for run in self._store.list_runs():
            if run.expires_at < now:
                self._store.delete_run(run.run_id)



# Default instance - use_celery controlled via SANDBOX_USE_CELERY env var
sandbox_service = SandboxService(use_celery=get_settings().sandbox_use_celery)

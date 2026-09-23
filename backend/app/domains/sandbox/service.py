import logging
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Any

logger = logging.getLogger(__name__)

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
    SandboxAiFeedbackResponse,
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

        run_id = f"run_{token_urlsafe(16)}"
        try:
            waiting = reserve_execution_slots(1, owner=run_id)
        except QueueFullError:
            return None, session, 503

        now = datetime.now(UTC)
        self._store.record_upload(session, now)

        record = SandboxRunRecord(
            run_id=run_id,
            session_id=session,
            course_id=course_id,
            assignment_id=assignment_id,
            queue_position=max(1, waiting),
            max_score=max_score,
        )
        try:
            self._store.save_run(record)
        except Exception:
            release_execution_slots(owner=run_id)
            return None, session, 503


        # Store execution payload on record
        if zip_data is not None and config_json is not None:
            import base64

            zip_b64 = base64.b64encode(zip_data).decode("ascii")
            record.zip_data_b64 = zip_b64
            record.config_json = config_json
            record.artifact_refs = artifact_refs or {}
            record.allowed_concepts = allowed_concepts or []
            record.stdin = stdin

            if self._use_celery:
                from app.domains.runs.tasks import grade_sandbox_run, set_run_state

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
                try:
                    self._store.save_run(record)
                    grade_result = grade_sandbox_run.delay(
                        run_id=run_id,
                        zip_data_b64=zip_b64,
                        config_json=config_json,
                        artifact_refs=artifact_refs or {},
                        allowed_concepts=allowed_concepts or [],
                        stdin=stdin,
                    )
                    record.celery_task_id = grade_result.id
                    self._store.save_run(record)
                except Exception:
                    from app.domains.runs.queue_admission import cancel_waiting
                    cancel_waiting(run_id)
                    return None, session, 503

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
        if self._use_celery:
            from app.domains.runs.queue_admission import ticket_state
            if ticket_state(run_id) == "expired":
                from app.domains.runs.orchestrator import set_run_state
                set_run_state(run_id, "failure", {"failure_category": "execution_interrupted",
                    "failure_message": "Execution was interrupted. Submit again."})

        # Try Redis first if Celery mode is active
        if self._use_celery:
            try:
                from app.domains.runs.tasks import get_run_state
                redis_state = get_run_state(run_id)
                if redis_state is not None:
                    state = redis_state.get("state", "queue")
                    queue_pos = redis_state.get("queue_position")
                    message = redis_state.get("failure_message") or self._message_for(state)
                    return RunStatusResponse(
                        run_id=run_id,
                        state=state,
                        queue_position=queue_pos if state == "queue" else None,
                        eta_band=eta_band_for_position(queue_pos)
                        if state == "queue"
                        else None,
                        counters=self._counters(),
                        backpressure=self._backpressure(),
                        message=message,
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

        from app.domains.runs.queue_admission import cancel_waiting
        if not cancel_waiting(run_id):
            return "not_cancelable"
        record.state = "failure"

        try:
            if self._use_celery:
                try:
                    from app.domains.runs.orchestrator import mark_run_cancelled, set_run_state
                    from app.integrations.celery.app import celery_app

                    mark_run_cancelled(run_id)
                    set_run_state(run_id, "failure", {"failure_category": "cancelled"})
                    if record.celery_task_id:
                        celery_app.control.revoke(record.celery_task_id, terminate=False)
                except Exception:
                    pass
        finally:
            release_execution_slots(owner=run_id)

        return SandboxCancelResponse(
            run_id=run_id,
            state="failure",
            counters=self._counters(),
            backpressure=self._backpressure(),
            message="Queued sandbox run cancelled before execution started.",
        )

    def _prepare_ai_feedback_context(self, record: SandboxRunRecord) -> dict[str, Any]:
        # Extract files from stored submission zip
        code_files: dict[str, str] = {}
        if record.zip_data_b64:
            try:
                import base64
                import io
                import zipfile

                raw_zip = base64.b64decode(record.zip_data_b64)
                with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
                    for name in zf.namelist():
                        if name.endswith(".py") and not name.startswith("__MACOSX"):
                            try:
                                code_files[name] = zf.read(name).decode("utf-8", errors="replace")
                            except Exception:
                                pass
            except Exception:
                pass

        # Retrieve test results and execution failure details
        test_results = []
        warnings = []
        failure_message = None

        if self._use_celery:
            try:
                from app.domains.runs.tasks import get_run_result

                redis_result = get_run_result(record.run_id)
                if redis_result:
                    test_results = redis_result.get("test_results", [])
                    failure_message = redis_result.get("failure_message")
                    for w in redis_result.get("warnings", []):
                        if isinstance(w, dict):
                            warnings.append(w)
            except Exception:
                pass

        if not test_results and record.result:
            test_results = record.result.get("test_results", [])
            failure_message = record.result.get("failure_message")

        assignment_title = record.assignment_id
        if record.config_json and isinstance(record.config_json, dict):
            assignment_title = record.config_json.get("title") or record.assignment_id

        from app.integrations.ai.prompts import requirements_from_config

        return {
            "assignment_title": assignment_title,
            "code_files": code_files,
            "test_results": test_results,
            "allowed_concepts": record.allowed_concepts,
            "warnings": warnings,
            "failure_message": failure_message,
            "requirements": requirements_from_config(record.config_json),
        }

    def generate_ai_feedback(
        self, run_id: str, session_id: str | None
    ) -> SandboxAiFeedbackResponse | str | None:
        self._expire_old_runs()
        record = self._store.get_run(run_id)
        if record is None or record.session_id != session_id:
            return None

        ctx = self._prepare_ai_feedback_context(record)
        from app.integrations.llm.client import LocalLLMClient

        llm_client = LocalLLMClient()
        feedback_text = llm_client.generate_sandbox_feedback(**ctx)

        return SandboxAiFeedbackResponse(
            run_id=run_id,
            ai_feedback=feedback_text,
            model=llm_client.model,
        )

    def generate_ai_feedback_stream(
        self, run_id: str, session_id: str | None
    ):
        self._expire_old_runs()
        record = self._store.get_run(run_id)
        if record is None or record.session_id != session_id:
            return None

        ctx = self._prepare_ai_feedback_context(record)
        from app.integrations.llm.client import LocalLLMClient

        llm_client = LocalLLMClient()
        return llm_client.generate_sandbox_feedback_stream(**ctx)

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

        # In offline/mock mode, evaluate synchronously when complete if result is not yet computed
        if record.result is None and record.zip_data_b64 and record.config_json:
            from app.domains.runs.orchestrator import execute_sandbox_run

            try:
                record.result = execute_sandbox_run(
                    run_id=run_id,
                    zip_data_b64=record.zip_data_b64,
                    config_json=record.config_json,
                    artifact_refs=record.artifact_refs or {},
                    allowed_concepts=record.allowed_concepts or [],
                    stdin=record.stdin,
                )
            except Exception:
                logger.exception("Synchronous sandbox evaluation failed for %s", run_id)

        # Check stored result from execution
        if record.result is not None:
            res_data = record.result
            test_summaries = []
            for tr in res_data.get("test_results", []):
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
                for w in res_data.get("warnings", [])
            ]
            if not res_data.get("success") and res_data.get("failure_message"):
                warnings.append(
                    SandboxWarning(
                        code=res_data.get("failure_category", "submission_error"),
                        message=str(res_data.get("failure_message") or "Execution failed."),
                    )
                )

            return SandboxRunResultResponse(
                run_id=run_id,
                state="complete" if res_data.get("success", True) else "failure",
                projected_score=res_data.get("score", 0),
                max_score=res_data.get("max_score", record.max_score),
                warnings=warnings,
                test_summaries=test_summaries,
                sanitized_feedback=str(res_data.get("failure_message") or "Execution failed.") if not res_data.get("success") else "Review your results above.",
                file_preview=self._file_preview(),
                raw_output=res_data.get("raw_output"),
            )

        return SandboxRunResultResponse(
            run_id=run_id,
            state="complete",
            projected_score=0,
            max_score=self._assignment_max_score(record),
            warnings=[
                SandboxWarning(
                    code="missing_files",
                    message="No valid submission files were uploaded or evaluated.",
                )
            ],
            test_summaries=[],
            sanitized_feedback="Upload assignment files to receive a projected score.",
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
            release_execution_slots(owner=record.run_id)

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

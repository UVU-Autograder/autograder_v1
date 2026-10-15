"""Overload behaviour: live queue counts, coded retryable errors, and the AI capacity limit."""

import threading
import time
from unittest.mock import MagicMock

import anyio
import pytest
from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.domains.runs.orchestrator import set_run_state
from app.domains.runs.queue_admission import QueueFullError, queue_snapshot, reserve_execution_slots, ticket_state
from app.domains.sandbox.ai_capacity import AiBusy, AiCapacity
from app.domains.sandbox.service import GRADER_FAULT_MESSAGE, sandbox_service
from app.integrations.llm.client import FeedbackOutcome


@pytest.fixture(autouse=True)
def celery_mode(reset_database, reset_sandbox_state, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "artifact_storage_dir", str(tmp_path / "artifacts"))
    monkeypatch.setattr("app.domains.runs.tasks.grade_sandbox_run.delay", MagicMock(return_value=MagicMock(id="task")))
    monkeypatch.setattr(sandbox_service, "_use_celery", True)
    yield


def create_run(client: TestClient, session: str | None = None):
    headers = {"X-Sandbox-Session": session} if session else {}
    return client.post(
        "/sandbox/courses/cs1400/assignments/simple-python-functions/runs",
        files={"bundle": ("submission.zip", b"print('synthetic')", "application/zip")},
        headers=headers,
    )


def test_snapshot_counts_submissions_ahead_without_identities():
    for owner in ("first", "second", "third"):
        reserve_execution_slots(1, owner=owner)
        time.sleep(0.002)  # distinct created_at
    assert queue_snapshot("first").ahead == 0
    assert queue_snapshot("second").ahead == 1
    third = queue_snapshot("third")
    assert third.ahead == 2 and third.waiting == 3 and third.owner_state == "waiting"
    assert queue_snapshot().ahead is None


def test_status_reports_live_position_and_wait_estimate(client, monkeypatch):
    reserve_execution_slots(1, owner="earlier_submission")
    time.sleep(0.002)
    created = create_run(client)
    assert created.status_code == 202, created.text
    run_id = created.json()["run_id"]
    body = client.get(f"/runs/{run_id}/status").json()
    assert body["state"] == "queue"
    assert body["submissions_ahead"] == 1
    assert body["queue_position"] == 2
    assert body["eta_seconds"] >= 1

    monkeypatch.setattr(get_settings(), "sandbox_show_queue_ahead", False)
    hidden = client.get(f"/runs/{run_id}/status").json()
    assert hidden["submissions_ahead"] is None and hidden["eta_seconds"] >= 1


def test_status_poll_never_releases_the_slot_when_redis_fails(client, monkeypatch):
    run_id = create_run(client).json()["run_id"]

    def broken(*args, **kwargs):
        raise ConnectionError("redis down")

    monkeypatch.setattr("app.domains.runs.tasks.get_run_state", broken)
    for _ in range(3):
        assert client.get(f"/runs/{run_id}/status").status_code == 200
    assert ticket_state(run_id) == "waiting"


def test_grader_faults_get_a_neutral_message(client):
    run_id = create_run(client).json()["run_id"]
    set_run_state(run_id, "failure", {
        "failure_category": "cleanup_failure",
        "failure_message": "Judge0 at http://127.0.0.1:2358 returned 400 for token abc",
    })
    body = client.get(f"/runs/{run_id}/status").json()
    assert body["grader_fault"] is True
    assert body["message"] == GRADER_FAULT_MESSAGE
    assert "2358" not in str(body)


def test_full_queue_is_retryable_and_not_counted(client, monkeypatch):
    session = "sandbox_overload_test"

    def full(*args, **kwargs):
        raise QueueFullError("full")

    monkeypatch.setattr("app.domains.sandbox.service.reserve_execution_slots", full)
    response = create_run(client, session=session)
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["code"] == "queue_full" and detail["retry_after_seconds"] > 0
    assert sandbox_service.quota_for_session(session).remaining == get_settings().sandbox_upload_limit


def test_ai_feedback_waits_for_grading_and_skips_grader_faults(client):
    created = create_run(client)
    run_id, session = created.json()["run_id"], created.headers["X-Sandbox-Session"]
    headers = {"X-Sandbox-Session": session}

    waiting = client.post(f"/sandbox/runs/{run_id}/ai-feedback", headers=headers)
    assert waiting.status_code == 409 and waiting.json()["detail"]["code"] == "grading_not_complete"

    set_run_state(run_id, "failure", {"failure_category": "judge0_error"})
    fault = client.post(f"/sandbox/runs/{run_id}/ai-feedback/stream", headers=headers)
    assert fault.status_code == 409 and fault.json()["detail"]["code"] == "grader_fault"


@pytest.mark.parametrize(
    ("outcome", "status", "code"),
    [("timeout", 504, "ai_timeout"), ("unreachable", 503, "ai_unavailable"), ("error", 503, "ai_error")],
)
def test_model_outages_are_coded_errors(client, monkeypatch, outcome, status, code):
    created = create_run(client)
    run_id, session = created.json()["run_id"], created.headers["X-Sandbox-Session"]
    set_run_state(run_id, "complete")
    monkeypatch.setattr(
        "app.integrations.llm.client.LocalLLMClient.generate_sandbox_feedback_outcome",
        lambda self, **ctx: FeedbackOutcome(outcome, "unused"),
    )
    response = client.post(f"/sandbox/runs/{run_id}/ai-feedback", headers={"X-Sandbox-Session": session})
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert int(response.headers["Retry-After"]) > 0


def test_ai_feedback_success_streams_lines(client, monkeypatch):
    created = create_run(client)
    run_id, session = created.json()["run_id"], created.headers["X-Sandbox-Session"]
    set_run_state(run_id, "complete")
    monkeypatch.setattr(
        "app.integrations.llm.client.LocalLLMClient.generate_sandbox_feedback_outcome",
        lambda self, **ctx: FeedbackOutcome("ok", "Line one\nLine two\n"),
    )
    response = client.post(f"/sandbox/runs/{run_id}/ai-feedback/stream", headers={"X-Sandbox-Session": session})
    assert response.status_code == 200
    assert response.text == "Line one\nLine two\n"


def _hold_capacity(monkeypatch, *, concurrent: int, waiting: int, wait_seconds: float):
    settings = get_settings()
    monkeypatch.setattr(settings, "ai_max_concurrent", concurrent)
    monkeypatch.setattr(settings, "ai_max_waiting", waiting)
    monkeypatch.setattr(settings, "ai_max_wait_seconds", wait_seconds)


def test_ai_capacity_turns_away_requests_beyond_the_waiting_limit(monkeypatch):
    _hold_capacity(monkeypatch, concurrent=1, waiting=0, wait_seconds=5)
    capacity = AiCapacity()
    release = threading.Event()
    outcomes: list[str] = []

    async def scenario():
        async def first():
            outcomes.append(await capacity.run(lambda: (release.wait(5), "first")[1]))

        async with anyio.create_task_group() as tg:
            tg.start_soon(first)
            await anyio.sleep(0.005)
            with pytest.raises(AiBusy) as busy:
                await capacity.run(lambda: "second")
            assert busy.value.retry_after_seconds >= 5
            release.set()

    anyio.run(scenario)
    assert outcomes == ["first"]


def test_ai_capacity_waits_then_gives_up(monkeypatch):
    _hold_capacity(monkeypatch, concurrent=1, waiting=1, wait_seconds=0.02)
    capacity = AiCapacity()
    release = threading.Event()

    async def scenario():
        async with anyio.create_task_group() as tg:
            tg.start_soon(capacity.run, lambda: release.wait(5))
            await anyio.sleep(0.005)
            started = time.monotonic()
            with pytest.raises(AiBusy):
                await capacity.run(lambda: "late")
            assert time.monotonic() - started >= 0.015
            release.set()
        assert capacity.waiting == 0 and capacity.running == 0

    anyio.run(scenario)


def test_grade_time_window_feeds_the_estimate(mock_redis_global):
    from app.domains.runs.orchestrator import GRADE_SECONDS_WINDOW, mean_grade_seconds, record_grade_seconds

    for seconds in [4.0] * (GRADE_SECONDS_WINDOW + 5):
        record_grade_seconds(seconds)
    assert len(mock_redis_global.data["sandbox:grade_seconds"]) == GRADE_SECONDS_WINDOW
    assert mean_grade_seconds() == pytest.approx(4.0)


def test_estimate_uses_observed_throughput_when_slower_than_ideal(monkeypatch):
    from app.domains.runs.queue_admission import eta_seconds_for

    monkeypatch.setattr(get_settings(), "judge0_max_concurrent", 2)
    assert eta_seconds_for(3, 6.0) == 12  # ideal: 2 rounds of 6 s
    assert eta_seconds_for(3, 6.0, throughput_per_second=0.1) == 40  # observed: 4 runs at 0.1/s
    assert eta_seconds_for(3, 6.0, throughput_per_second=10.0) == 12  # never below the ideal


def test_throughput_needs_several_recent_completions(mock_redis_global):
    from app.domains.runs.orchestrator import recent_throughput_per_second

    assert recent_throughput_per_second() is None
    base = time.time()
    mock_redis_global.data["sandbox:completions"] = [f"{base - i * 5:.3f}" for i in range(5)]
    assert recent_throughput_per_second() == pytest.approx(0.2)


def test_grading_task_retries_when_scheduling_is_briefly_unavailable(monkeypatch):
    from celery.exceptions import Retry
    from fastapi import HTTPException

    from app.domains.runs import tasks

    def unavailable(*args, **kwargs):
        raise HTTPException(503, "Scheduling is unavailable. Retry later.")

    monkeypatch.setattr("app.domains.runs.queue_admission.claim", unavailable)
    with pytest.raises(Retry):
        tasks.grade_sandbox_run.apply(kwargs={
            "run_id": "run_x", "zip_data_b64": "", "config": {}, "artifact_refs": {}, "allowed_concepts": [],
        }, throw=True)


def test_network_limit_counts_runs_per_address_and_refunds_unadmitted_ones(client, monkeypatch, mock_redis_global):
    from app.domains.sandbox import ip_limit

    assert ip_limit.client_ip("127.0.0.1", "10.8.0.7") == "10.8.0.7"  # through nginx
    assert ip_limit.client_ip("203.0.113.9", "10.8.0.7") == "203.0.113.9"  # header not trusted
    monkeypatch.setattr(get_settings(), "sandbox_ip_hourly_limit", 2)
    monkeypatch.setattr(get_settings(), "sandbox_upload_limit", 20)

    def from_network(session):
        headers = {"X-Sandbox-Session": session, "X-Real-IP": "10.8.0.7"}
        return client.post(
            "/sandbox/courses/cs1400/assignments/simple-python-functions/runs",
            files={"bundle": ("submission.zip", b"print('synthetic')", "application/zip")},
            headers=headers,
        )

    # The TestClient's peer is "testclient", so pin the address the router sees.
    monkeypatch.setattr(ip_limit, "client_ip", lambda peer, header: header)
    assert from_network("tab-a").status_code == 202
    assert from_network("tab-b").status_code == 202  # a new tab does not reset the network count
    blocked = from_network("tab-c")
    assert blocked.status_code == 429 and blocked.json()["detail"]["code"] == "network_limit"

    monkeypatch.setattr(get_settings(), "sandbox_ip_hourly_limit", 3)
    monkeypatch.setattr(
        "app.domains.sandbox.service.reserve_execution_slots",
        lambda *a, **k: (_ for _ in ()).throw(QueueFullError("full")),
    )
    assert from_network("tab-d").status_code == 503
    counter = next(v for k, v in mock_redis_global.data.items() if k.startswith("sandbox:ip:10.8.0.7:"))
    assert counter == "2"  # the queue-full run was given back


def test_network_limit_is_off_by_default_and_skips_the_allowlist(monkeypatch, mock_redis_global):
    from app.domains.sandbox import ip_limit

    assert get_settings().sandbox_ip_hourly_limit == 0
    assert ip_limit.charge("10.8.0.7") is None and not mock_redis_global.data
    monkeypatch.setattr(get_settings(), "sandbox_ip_hourly_limit", 1)
    monkeypatch.setattr(get_settings(), "sandbox_ip_allowlist", "10.8.0.99")
    assert ip_limit.charge("10.8.0.99") is None and ip_limit.charge("10.8.0.99") is None
    assert ip_limit.charge("10.8.0.7") is None
    limited = ip_limit.charge("10.8.0.7")
    assert limited is not None and limited.limit == 1 and limited.reset_at
    ip_limit.refund("10.8.0.7")
    assert ip_limit.charge("10.8.0.7") is None


def test_quota_reads_never_rewrite_and_uploads_keep_only_what_can_count(monkeypatch, mock_redis_global):
    from datetime import UTC, datetime, timedelta

    from app.domains.sandbox.store import RedisRunStateStore

    monkeypatch.setattr(get_settings(), "sandbox_upload_limit", 3)
    store = RedisRunStateStore()
    now = datetime.now(UTC)
    for minutes in (50, 40, 30, 20, 10):
        store.record_upload("tab", now - timedelta(minutes=minutes))
    assert len(mock_redis_global.data["sandbox:uploads:tab"]) == 3  # older entries can never count again
    before = list(mock_redis_global.data["sandbox:uploads:tab"])
    quota = store.get_quota("tab", 3, timedelta(hours=1))
    assert quota.remaining == 0 and mock_redis_global.data["sandbox:uploads:tab"] == before

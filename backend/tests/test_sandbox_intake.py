"""Unit tests for the deep SandboxIntakeEngine domain module."""
from __future__ import annotations

import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.domains.runs.queue_admission import QueueFullError
from app.domains.sandbox.intake import (
    AssignmentNotGradableError,
    AssignmentNotFoundError,
    GradingQueueFullError,
    NetworkRateLimitExceededError,
    SandboxIntakeEngine,
    SessionQuotaExceededError,
)
from app.domains.sandbox.schemas import QueueBackpressure, UploadQuota
from app.domains.sandbox.service import SandboxService
from app.domains.sandbox.store import InMemoryRunStateStore


@pytest.fixture
def mock_db() -> MagicMock:
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def intake_engine() -> SandboxIntakeEngine:
    store = InMemoryRunStateStore()
    service = SandboxService(use_celery=False, store=store)
    return SandboxIntakeEngine(service=service)


@pytest.fixture
def sample_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("main.py", "def add(a, b): return a + b\n")
    return buf.getvalue()


def test_intake_raises_assignment_not_found(intake_engine: SandboxIntakeEngine, mock_db: MagicMock, sample_zip: bytes):
    with patch("app.domains.sandbox.intake.get_assignment_for_course", return_value=None):
        with pytest.raises(AssignmentNotFoundError) as exc_info:
            intake_engine.intake_submission(
                mock_db,
                course_id="nonexistent",
                assignment_id="missing",
                session_id=None,
                zip_data=sample_zip,
            )
        assert exc_info.value.course_id == "nonexistent"
        assert exc_info.value.assignment_id == "missing"


def test_intake_raises_preflight_not_gradable(intake_engine: SandboxIntakeEngine, mock_db: MagicMock, sample_zip: bytes):
    mock_assignment = MagicMock()
    mock_assignment.config = MagicMock()

    with (
        patch("app.domains.sandbox.intake.get_assignment_for_course", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.get_sandbox_assignment", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.run_preflight_validation", return_value=["Preflight error"]),
    ):
        with pytest.raises(AssignmentNotGradableError) as exc_info:
            intake_engine.intake_submission(
                mock_db,
                course_id="cs1400",
                assignment_id="lab1",
                session_id=None,
                zip_data=sample_zip,
            )
        assert "not ready for grading" in exc_info.value.message


def test_intake_raises_session_quota_exceeded(intake_engine: SandboxIntakeEngine, mock_db: MagicMock, sample_zip: bytes):
    mock_assignment = MagicMock()
    mock_assignment.config = MagicMock()
    mock_assignment.artifacts = []
    mock_assignment.max_score = 100

    exhausted_quota = UploadQuota(limit=5, remaining=0, reset_at="2026-10-20T15:00:00Z", window_seconds=3600)

    with (
        patch("app.domains.sandbox.intake.get_assignment_for_course", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.get_sandbox_assignment", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.run_preflight_validation", return_value=[]),
        patch("app.domains.sandbox.intake.inventory_status", return_value="ready"),
        patch("app.domains.sandbox.intake.effective_allowed_concepts", return_value=[]),
        patch.object(intake_engine._service, "quota_for_session", return_value=exhausted_quota),
    ):
        with pytest.raises(SessionQuotaExceededError) as exc_info:
            intake_engine.intake_submission(
                mock_db,
                course_id="cs1400",
                assignment_id="lab1",
                session_id="session_exhausted",
                zip_data=sample_zip,
            )
        assert exc_info.value.quota.remaining == 0
        mock_db.close.assert_called_once()


def test_intake_raises_network_rate_limit_exceeded(intake_engine: SandboxIntakeEngine, mock_db: MagicMock, sample_zip: bytes):
    mock_assignment = MagicMock()
    mock_assignment.config = MagicMock()
    mock_assignment.artifacts = []
    mock_assignment.max_score = 100

    available_quota = UploadQuota(limit=5, remaining=5, reset_at="2026-10-20T15:00:00Z", window_seconds=3600)
    mock_limited = MagicMock(limit=10, reset_at="2026-10-20T16:00:00Z")

    with (
        patch("app.domains.sandbox.intake.get_assignment_for_course", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.get_sandbox_assignment", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.run_preflight_validation", return_value=[]),
        patch("app.domains.sandbox.intake.inventory_status", return_value="ready"),
        patch("app.domains.sandbox.intake.effective_allowed_concepts", return_value=[]),
        patch.object(intake_engine._service, "quota_for_session", return_value=available_quota),
        patch("app.domains.sandbox.intake.ip_limit.charge", return_value=mock_limited),
    ):
        with pytest.raises(NetworkRateLimitExceededError) as exc_info:
            intake_engine.intake_submission(
                mock_db,
                course_id="cs1400",
                assignment_id="lab1",
                session_id="session_test",
                zip_data=sample_zip,
                client_ip="192.168.1.100",
            )
        assert exc_info.value.limit == 10
        assert exc_info.value.reset_at == "2026-10-20T16:00:00Z"
        mock_db.close.assert_called_once()


def test_intake_raises_queue_full_and_refunds(intake_engine: SandboxIntakeEngine, mock_db: MagicMock, sample_zip: bytes):
    mock_assignment = MagicMock()
    mock_assignment.config = MagicMock()
    mock_assignment.artifacts = []
    mock_assignment.max_score = 100

    available_quota = UploadQuota(limit=5, remaining=5, reset_at="2026-10-20T15:00:00Z", window_seconds=3600)

    with (
        patch("app.domains.sandbox.intake.get_assignment_for_course", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.get_sandbox_assignment", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.run_preflight_validation", return_value=[]),
        patch("app.domains.sandbox.intake.inventory_status", return_value="ready"),
        patch("app.domains.sandbox.intake.effective_allowed_concepts", return_value=[]),
        patch.object(intake_engine._service, "quota_for_session", return_value=available_quota),
        patch.object(
            intake_engine._service,
            "_backpressure",
            return_value=QueueBackpressure(
                high_load_threshold=10,
                full_queue_threshold=20,
                current_waiting=0,
                high_load=False,
                accepting_runs=True,
            ),
        ),
        patch("app.domains.sandbox.intake.ip_limit.charge", return_value=None),
        patch("app.domains.sandbox.intake.ip_limit.refund") as mock_refund,
        patch("app.domains.sandbox.intake.reserve_execution_slots", side_effect=QueueFullError("full")),
    ):
        with pytest.raises(GradingQueueFullError) as exc_info:
            intake_engine.intake_submission(
                mock_db,
                course_id="cs1400",
                assignment_id="lab1",
                session_id="session_test",
                zip_data=sample_zip,
                client_ip="10.0.0.1",
            )
        assert exc_info.value.retry_after_seconds == 15
        mock_refund.assert_called_once_with("10.0.0.1")
        mock_db.close.assert_called_once()


def test_intake_success_closes_db_and_returns_result(intake_engine: SandboxIntakeEngine, mock_db: MagicMock, sample_zip: bytes):
    mock_assignment = MagicMock()
    mock_assignment.config = MagicMock()
    mock_assignment.config.config = {"entrypoint": "main.py"}
    mock_assignment.config.validated_test_manifest = None
    mock_assignment.artifacts = []
    mock_assignment.max_score = 100
    mock_assignment.description = "Test description"

    available_quota = UploadQuota(limit=5, remaining=5, reset_at="2026-10-20T15:00:00Z", window_seconds=3600)

    with (
        patch("app.domains.sandbox.intake.get_assignment_for_course", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.get_sandbox_assignment", return_value=mock_assignment),
        patch("app.domains.sandbox.intake.run_preflight_validation", return_value=[]),
        patch("app.domains.sandbox.intake.inventory_status", return_value="ready"),
        patch("app.domains.sandbox.intake.effective_allowed_concepts", return_value=["variables"]),
        patch.object(intake_engine._service, "quota_for_session", return_value=available_quota),
        patch.object(
            intake_engine._service,
            "_backpressure",
            return_value=QueueBackpressure(
                high_load_threshold=10,
                full_queue_threshold=20,
                current_waiting=0,
                high_load=False,
                accepting_runs=True,
            ),
        ),
        patch("app.domains.sandbox.intake.ip_limit.charge", return_value=None),
        patch("app.domains.sandbox.intake.reserve_execution_slots", return_value=1),
    ):
        result = intake_engine.intake_submission(
            mock_db,
            course_id="cs1400",
            assignment_id="lab1",
            session_id="my_session",
            zip_data=sample_zip,
            stdin="input_data",
            client_ip="10.0.0.1",
        )

        assert result.session_id == "my_session"
        assert result.response.run_id.startswith("run_")
        assert result.response.status_url.startswith("/runs/")
        assert result.response.result_url.startswith("/sandbox/runs/")
        mock_db.close.assert_called_once()

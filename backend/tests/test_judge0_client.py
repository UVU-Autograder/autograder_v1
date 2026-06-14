"""Tests for the Judge0 async client.

All HTTP interactions are mocked — no real network requests are made.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.integrations.judge0.client import (  # noqa: E402
    JUDGE0_STATUS_MAP,
    Judge0CleanupError,
    Judge0Client,
    Judge0TimeoutError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_response(data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock ``httpx.Response`` with the given JSON body."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client_no_auth() -> Judge0Client:
    """Judge0Client without an auth token."""
    return Judge0Client(base_url="http://judge0:2358")


@pytest.fixture
def client_with_auth() -> Judge0Client:
    """Judge0Client with an auth token."""
    return Judge0Client(base_url="http://judge0:2358", auth_token="secret-token")


# ---------------------------------------------------------------------------
# 1. create_submission – basic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_submission_sends_correct_post_and_returns_token(
    client_no_auth: Judge0Client,
) -> None:
    mock_response = _json_response({"token": "abc-123"}, status_code=201)
    client_no_auth._client.post = AsyncMock(return_value=mock_response)

    token = await client_no_auth.create_submission(
        source_code='print("hi")',
        language_id=71,
    )

    assert token == "abc-123"

    call_kwargs = client_no_auth._client.post.call_args
    assert call_kwargs.args[0] == "/submissions"
    body = call_kwargs.kwargs["json"]
    assert body["source_code"] == 'print("hi")'
    assert body["language_id"] == 71
    assert body["cpu_time_limit"] == 10.0
    assert body["wall_time_limit"] == 20.0
    assert body["memory_limit"] == 262144
    assert "additional_files" not in body
    assert "stdin" not in body

    params = call_kwargs.kwargs["params"]
    assert params["base64_encoded"] == "false"
    assert params["wait"] == "false"


# ---------------------------------------------------------------------------
# 2. create_submission – with additional_files
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_submission_includes_additional_files_when_provided(
    client_no_auth: Judge0Client,
) -> None:
    mock_response = _json_response({"token": "def-456"})
    client_no_auth._client.post = AsyncMock(return_value=mock_response)

    token = await client_no_auth.create_submission(
        source_code="code",
        language_id=71,
        additional_files_b64="base64data==",
        stdin="test input\n",
    )

    assert token == "def-456"

    body = client_no_auth._client.post.call_args.kwargs["json"]
    assert body["additional_files"] == "base64data=="
    assert body["stdin"] == "test input\n"


# ---------------------------------------------------------------------------
# 3. poll_submission – polls until terminal status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_submission_returns_result_when_status_above_two(
    client_no_auth: Judge0Client,
) -> None:
    queued = _json_response({"status": {"id": 1, "description": "In Queue"}})
    processing = _json_response({"status": {"id": 2, "description": "Processing"}})
    accepted = _json_response(
        {
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "hello\n",
            "time": "0.01",
        }
    )

    client_no_auth._client.get = AsyncMock(
        side_effect=[queued, processing, accepted]
    )

    # Use a tiny poll interval so the test runs fast.
    result = await client_no_auth.poll_submission(
        "abc-123", poll_interval=0.0, max_polls=10
    )

    assert result["status"]["id"] == 3
    assert result["stdout"] == "hello\n"
    assert client_no_auth._client.get.call_count == 3

    # Verify the GET URL and params of the last call.
    last_call = client_no_auth._client.get.call_args
    assert "abc-123" in last_call.args[0]
    assert last_call.kwargs["params"]["fields"] == "*"


# ---------------------------------------------------------------------------
# 4. poll_submission – timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_submission_raises_timeout_after_max_polls(
    client_no_auth: Judge0Client,
) -> None:
    still_processing = _json_response(
        {"status": {"id": 2, "description": "Processing"}}
    )
    client_no_auth._client.get = AsyncMock(return_value=still_processing)

    with pytest.raises(Judge0TimeoutError, match="timed out after 3 attempts"):
        await client_no_auth.poll_submission(
            "stuck-token", poll_interval=0.0, max_polls=3
        )

    assert client_no_auth._client.get.call_count == 3


# ---------------------------------------------------------------------------
# 5. delete_submission – success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_submission_returns_true_on_success(
    client_no_auth: Judge0Client,
) -> None:
    for code in (200, 204):
        resp = MagicMock()
        resp.status_code = code
        client_no_auth._client.delete = AsyncMock(return_value=resp)

        result = await client_no_auth.delete_submission("tok-del")
        assert result is True


# ---------------------------------------------------------------------------
# 6. delete_submission – failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_submission_raises_cleanup_error_on_failure(
    client_no_auth: Judge0Client,
) -> None:
    resp = MagicMock()
    resp.status_code = 404
    client_no_auth._client.delete = AsyncMock(return_value=resp)

    with pytest.raises(Judge0CleanupError, match="Unexpected status 404"):
        await client_no_auth.delete_submission("tok-gone")


# ---------------------------------------------------------------------------
# 7. Auth token header
# ---------------------------------------------------------------------------


def test_auth_token_is_included_in_headers_when_provided(
    client_with_auth: Judge0Client,
) -> None:
    headers = client_with_auth._client.headers
    assert headers["X-Auth-Token"] == "secret-token"


def test_auth_token_is_absent_when_not_provided(
    client_no_auth: Judge0Client,
) -> None:
    headers = client_no_auth._client.headers
    assert "X-Auth-Token" not in headers


# ---------------------------------------------------------------------------
# 8. Status mapping
# ---------------------------------------------------------------------------


def test_status_map_covers_key_judge0_codes() -> None:
    assert JUDGE0_STATUS_MAP[3] == "accepted"
    assert JUDGE0_STATUS_MAP[4] == "wrong_answer"
    assert JUDGE0_STATUS_MAP[5] == "timeout"
    assert JUDGE0_STATUS_MAP[6] == "compile_error"
    assert JUDGE0_STATUS_MAP[13] == "internal_error"
    assert JUDGE0_STATUS_MAP[14] == "compile_error"

    # All runtime-error codes (7-12) → "timeout"
    for sid in range(7, 13):
        assert JUDGE0_STATUS_MAP[sid] == "timeout", f"status {sid} should be 'timeout'"

    # Every value must be one of the known categories.
    valid_categories = {"accepted", "wrong_answer", "timeout", "compile_error", "internal_error"}
    for sid, category in JUDGE0_STATUS_MAP.items():
        assert category in valid_categories, f"unknown category '{category}' for status {sid}"

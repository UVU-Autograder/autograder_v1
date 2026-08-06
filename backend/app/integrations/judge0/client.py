"""Judge0 CE API client for sandboxed code execution.

Wraps httpx.AsyncClient to submit, poll, and delete Judge0 submissions
with structured error handling and configurable resource limits.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from typing_extensions import Self

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class Judge0Error(Exception):
    """Base exception for all Judge0 integration errors."""


class Judge0SubmissionError(Judge0Error):
    """Raised when submission creation fails."""


class Judge0TimeoutError(Judge0Error):
    """Raised when polling exceeds the maximum number of attempts."""


class Judge0CleanupError(Judge0Error):
    """Raised when submission deletion fails (launch-blocking)."""


# ---------------------------------------------------------------------------
# Status mapping – Judge0 status IDs → autograder failure categories
# ---------------------------------------------------------------------------

JUDGE0_STATUS_MAP: dict[int, str] = {
    3: "accepted",        # Accepted
    4: "wrong_answer",    # Wrong Answer
    5: "timeout",         # Time Limit Exceeded
    6: "compile_error",   # Compilation Error
    7: "timeout",         # Runtime Error (SIGSEGV)
    8: "timeout",         # Runtime Error (SIGXFSZ)
    9: "timeout",         # Runtime Error (SIGFPE)
    10: "timeout",        # Runtime Error (SIGABRT)
    11: "timeout",        # Runtime Error (NZEC)
    12: "timeout",        # Runtime Error (Other)
    13: "internal_error", # Internal Error
    14: "compile_error",  # Exec Format Error
}

_JUDGE0_FAILURE_MESSAGES: dict[str, str] = {
    "timeout": "Execution timed out.",
    "compile_error": "Code could not be compiled or imported.",
    "internal_error": "Execution engine internal error.",
}


def judge0_failure_for_status(status_id: int) -> tuple[str, str] | None:
    """Return ``(category, message)`` for a Judge0-level failure, else ``None``.

    ``accepted`` / ``wrong_answer`` (and unknown IDs) return ``None`` so callers
    parse runner stdout — pytest remains the scoring ground truth.
    """
    category = JUDGE0_STATUS_MAP.get(status_id)
    if category is None or category in ("accepted", "wrong_answer"):
        return None
    return category, _JUDGE0_FAILURE_MESSAGES.get(
        category, f"Judge0 execution failed with status {status_id}."
    )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class Judge0Client:
    """Async client for the Judge0 CE REST API.

    Parameters
    ----------
    base_url:
        Root URL of the Judge0 instance (e.g. ``http://localhost:2358``).
    auth_token:
        Optional authentication token sent as ``X-Auth-Token`` header.
    """

    def __init__(self, base_url: str, auth_token: str | None = None) -> None:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if auth_token is not None:
            headers["X-Auth-Token"] = auth_token

        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=30.0,
        )

    # -- public API ----------------------------------------------------------

    async def create_submission(
        self,
        source_code: str,
        language_id: int,
        additional_files_b64: str | None = None,
        stdin: str | None = None,
        cpu_time_limit: float = 10.0,
        wall_time_limit: float = 20.0,
        memory_limit: int = 262144,
    ) -> str:
        """Submit code to Judge0 for execution.

        Parameters
        ----------
        source_code:
            Raw source code to execute.
        language_id:
            Judge0 language identifier.
        additional_files_b64:
            Base-64 encoded additional files archive, if any.
        stdin:
            Standard input to feed to the program.
        cpu_time_limit:
            CPU time limit in seconds.
        wall_time_limit:
            Wall-clock time limit in seconds.
        memory_limit:
            Memory limit in kilobytes.

        Returns
        -------
        str
            The submission token assigned by Judge0.

        Raises
        ------
        Judge0SubmissionError
            If the POST request fails or the response is missing a token.
        """
        body: dict[str, Any] = {
            "source_code": source_code,
            "language_id": language_id,
            "cpu_time_limit": cpu_time_limit,
            "wall_time_limit": wall_time_limit,
            "memory_limit": memory_limit,
        }

        if additional_files_b64 is not None:
            body["additional_files"] = additional_files_b64

        if stdin is not None:
            body["stdin"] = stdin

        try:
            response = await self._client.post(
                "/submissions",
                params={"base64_encoded": "false", "wait": "false"},
                json=body,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise Judge0SubmissionError(
                f"Failed to create Judge0 submission: {exc}"
            ) from exc

        data = response.json()
        token = data.get("token")
        if not token:
            raise Judge0SubmissionError(
                "Judge0 response missing 'token' field"
            )
        return token

    async def poll_submission(
        self,
        token: str,
        poll_interval: float = 1.0,
        max_polls: int = 60,
    ) -> dict[str, Any]:
        """Poll a submission until it reaches a terminal state.

        Judge0 status IDs 1 (In Queue) and 2 (Processing) are non-terminal.
        This method keeps polling until ``status.id > 2``.

        Parameters
        ----------
        token:
            Submission token returned by :meth:`create_submission`.
        poll_interval:
            Seconds to wait between successive polls.
        max_polls:
            Maximum number of GET requests before giving up.

        Returns
        -------
        dict
            The full Judge0 submission result.

        Raises
        ------
        Judge0TimeoutError
            If *max_polls* is exceeded without reaching a terminal state.
        """
        for _ in range(max_polls):
            response = await self._client.get(
                f"/submissions/{token}",
                params={"base64_encoded": "false"},
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()

            status_id: int = data.get("status", {}).get("id", 0)
            if status_id > 2:
                return data

            await asyncio.sleep(poll_interval)

        raise Judge0TimeoutError(
            f"Polling timed out after {max_polls} attempts for token {token}"
        )

    async def delete_submission(self, token: str) -> bool:
        """Delete a submission from the Judge0 instance.

        Parameters
        ----------
        token:
            Submission token to delete.

        Returns
        -------
        bool
            ``True`` if the deletion succeeded.

        Raises
        ------
        Judge0CleanupError
            If the DELETE request fails.  This is launch-blocking per spec.
        """
        try:
            response = await self._client.delete(f"/submissions/{token}")
            if response.status_code in (200, 204):
                return True
            raise Judge0CleanupError(
                f"Unexpected status {response.status_code} when deleting "
                f"submission {token}"
            )
        except httpx.HTTPError as exc:
            raise Judge0CleanupError(
                f"Failed to delete Judge0 submission {token}: {exc}"
            ) from exc

    # -- lifecycle -----------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_judge0_client() -> Judge0Client:
    """Build a :class:`Judge0Client` from application settings."""
    from app.core.settings import get_settings

    settings = get_settings()
    return Judge0Client(
        base_url=settings.judge0_url,
        auth_token=settings.judge0_auth_token,
    )

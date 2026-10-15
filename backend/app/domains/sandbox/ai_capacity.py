"""Bounded admission for AI feedback requests.

Each feedback request holds a model slot for a few seconds of GPU time. Without a
limit, a burst of requests all queue inside vLLM and the slowest ones pass the
backend's 30 s model timeout, so students see "timed out" after a long wait; the
synchronous handlers also used the same 40-thread pool as status polling.

Here at most ``AI_MAX_CONCURRENT`` requests run at once, on their own threads.
Up to ``AI_MAX_WAITING`` more wait (each at most ``AI_MAX_WAIT_SECONDS``) for a
slot; anything beyond that is told "busy, retry in N s" straight away (HTTP 503,
code ``ai_busy``), which the sandbox UI turns into an automatic, backed-off retry.

The counts live in this process. The backend runs a single uvicorn process, so
this is effectively a global limit; with several processes it would be per process.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import anyio
import anyio.to_thread

from app.core.settings import get_settings

T = TypeVar("T")


class AiBusy(Exception):
    """No AI slot is free within the wait limit."""

    def __init__(self, ahead: int, retry_after_seconds: int) -> None:
        super().__init__("AI feedback is busy")
        self.ahead = ahead
        self.retry_after_seconds = retry_after_seconds


class AiCapacity:
    def __init__(self) -> None:
        self._size: int | None = None
        self._slots: anyio.CapacityLimiter | None = None
        self._threads: anyio.CapacityLimiter | None = None
        self.waiting = 0

    def _ensure(self) -> tuple[anyio.CapacityLimiter, anyio.CapacityLimiter]:
        size = get_settings().ai_max_concurrent
        if self._slots is None or self._threads is None or self._size != size:
            # Created lazily, inside the running event loop.
            self._slots = anyio.CapacityLimiter(size)
            self._threads = anyio.CapacityLimiter(size)
            self._size = size
        return self._slots, self._threads

    @property
    def running(self) -> int:
        return int(self._slots.borrowed_tokens) if self._slots is not None else 0

    def retry_after_seconds(self) -> int:
        size = self._size or get_settings().ai_max_concurrent
        # Each request takes a few seconds; scale with how far back in line a retry would land.
        return max(5, min(30, round(4 * (1 + self.waiting / size))))

    async def run(self, func: Callable[..., T], *args: Any) -> T:
        settings = get_settings()
        slots, threads = self._ensure()
        if slots.available_tokens == 0 and self.waiting >= settings.ai_max_waiting:
            raise AiBusy(ahead=self.waiting, retry_after_seconds=self.retry_after_seconds())
        ahead = self.waiting if slots.available_tokens == 0 else 0
        self.waiting += 1
        acquired = False
        try:
            with anyio.fail_after(settings.ai_max_wait_seconds):
                await slots.acquire()
            acquired = True
        except TimeoutError:
            raise AiBusy(ahead=ahead, retry_after_seconds=self.retry_after_seconds()) from None
        finally:
            self.waiting -= 1
        try:
            return await anyio.to_thread.run_sync(func, *args, limiter=threads)
        finally:
            if acquired:
                slots.release()


ai_capacity = AiCapacity()

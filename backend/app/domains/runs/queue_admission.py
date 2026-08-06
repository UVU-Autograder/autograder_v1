"""Shared Redis-backed execution-queue admission (warn@40 / reject@50)."""
from __future__ import annotations

from app.domains.runs.schemas import EtaBand, QueueBackpressure

HIGH_LOAD_THRESHOLD = 40
FULL_QUEUE_THRESHOLD = 50
_WAITING_KEY = "ag:exec_queue:waiting"

# Process-local fallback when Redis is unavailable (contract tests / offline).
_local_waiting = 0


class QueueFullError(Exception):
    """Raised when reserving would exceed FULL_QUEUE_THRESHOLD."""


def _redis():
    import redis

    from app.core.settings import get_settings

    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def waiting_count() -> int:
    global _local_waiting
    try:
        return int(_redis().get(_WAITING_KEY) or 0)
    except Exception:
        return _local_waiting


def reserve_execution_slots(count: int) -> int:
    """Atomically reserve *count* waiting slots. Returns new waiting total."""
    global _local_waiting
    if count < 1:
        return waiting_count()

    try:
        r = _redis()
        from redis.exceptions import WatchError

        for _ in range(20):
            try:
                pipe = r.pipeline()
                pipe.watch(_WAITING_KEY)
                current = int(r.get(_WAITING_KEY) or 0)
                if current + count > FULL_QUEUE_THRESHOLD:
                    pipe.unwatch()
                    raise QueueFullError(
                        f"Grading queue is full ({FULL_QUEUE_THRESHOLD} waiting jobs). "
                        "Retry later."
                    )
                pipe.multi()
                pipe.set(_WAITING_KEY, current + count)
                pipe.execute()
                return current + count
            except WatchError:
                continue
        raise QueueFullError(
            f"Grading queue is full ({FULL_QUEUE_THRESHOLD} waiting jobs). Retry later."
        )
    except QueueFullError:
        raise
    except Exception:
        if _local_waiting + count > FULL_QUEUE_THRESHOLD:
            raise QueueFullError(
                f"Grading queue is full ({FULL_QUEUE_THRESHOLD} waiting jobs). "
                "Retry later."
            )
        _local_waiting += count
        return _local_waiting


def release_execution_slots(count: int = 1) -> int:
    """Release *count* waiting slots (floor at 0). Returns new waiting total."""
    global _local_waiting
    if count < 1:
        return waiting_count()

    try:
        r = _redis()
        new_val = int(r.decrby(_WAITING_KEY, count))
        if new_val < 0:
            r.set(_WAITING_KEY, 0)
            return 0
        return new_val
    except Exception:
        _local_waiting = max(0, _local_waiting - count)
        return _local_waiting


def reset_admission_state_for_tests() -> None:
    """Clear local + Redis waiting counters (tests only)."""
    global _local_waiting
    _local_waiting = 0
    try:
        _redis().delete(_WAITING_KEY)
    except Exception:
        pass


def backpressure_snapshot() -> QueueBackpressure:
    waiting = waiting_count()
    return QueueBackpressure(
        high_load_threshold=HIGH_LOAD_THRESHOLD,
        full_queue_threshold=FULL_QUEUE_THRESHOLD,
        current_waiting=waiting,
        high_load=waiting >= HIGH_LOAD_THRESHOLD,
        accepting_runs=waiting < FULL_QUEUE_THRESHOLD,
    )


def eta_band_for_position(position: int | None) -> EtaBand | None:
    if position is None or position < 1:
        return None
    if position <= 2:
        return "under_1_min"
    if position <= 6:
        return "1_to_3_min"
    if position <= 10:
        return "3_to_5_min"
    return "over_5_min"

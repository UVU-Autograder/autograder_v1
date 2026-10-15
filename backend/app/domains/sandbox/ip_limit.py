"""Per-network cap on sandbox runs, on top of the per-tab quota.

The per-tab quota (SANDBOX_UPLOAD_LIMIT) starts over in a new browser tab, so on
its own it does not stop a script from submitting all day. This counts admitted
runs per client address in Redis, per window of SANDBOX_UPLOAD_WINDOW_SECONDS.

Off by default (SANDBOX_IP_HOURLY_LIMIT=0). The VPN or a campus NAT can put a
whole class behind one address, so look at the addresses in the nginx access log
during a lab before turning it on, and set it well above a class's total
(class size x the per-tab limit). SANDBOX_IP_ALLOWLIST exempts addresses, such
as the machine running the stress test.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.settings import get_settings

logger = logging.getLogger(__name__)

# The backend listens on loopback behind nginx, which sets X-Real-IP; only trust the
# header from there, never from a client that reached the API directly.
TRUSTED_PROXIES = {"127.0.0.1", "::1"}
KEY_PREFIX = "sandbox:ip:"


@dataclass(frozen=True)
class NetworkLimited:
    limit: int
    reset_at: str


def client_ip(peer: str | None, real_ip_header: str | None) -> str | None:
    """The student's address: nginx's X-Real-IP when the request came through nginx."""
    if peer in TRUSTED_PROXIES and real_ip_header:
        return real_ip_header.strip()
    return peer


def _window(now: float) -> tuple[int, int]:
    size = max(1, int(get_settings().sandbox_upload_window_seconds))
    start = int(now // size) * size
    return start, start + size


def _enabled_for(ip: str | None) -> bool:
    settings = get_settings()
    if settings.sandbox_ip_hourly_limit <= 0 or not ip:
        return False
    allow = {a.strip() for a in settings.sandbox_ip_allowlist.split(",") if a.strip()}
    return ip not in allow


def _redis():
    import redis

    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def charge(ip: str | None) -> NetworkLimited | None:
    """Count one run for ``ip``; returns the limit when it is used up (nothing counted then).

    Atomic (INCR), so simultaneous uploads cannot all slip under the limit. If Redis
    is unreachable the run is allowed: this is abuse protection, not the admission gate.
    """
    if not _enabled_for(ip):
        return None
    limit = get_settings().sandbox_ip_hourly_limit
    start, end = _window(time.time())
    key = f"{KEY_PREFIX}{ip}:{start}"
    try:
        r = _redis()
        count = r.incr(key)
        if count == 1:
            r.expire(key, end - start + 60)
        if count > limit:
            r.decr(key)
            return NetworkLimited(limit=limit, reset_at=datetime.fromtimestamp(end, tz=UTC).isoformat())
    except Exception:  # noqa: BLE001
        logger.warning("Per-network run limit unavailable; allowing the run")
    return None


def refund(ip: str | None) -> None:
    """Give back a run that was charged but not admitted (queue full, grader down)."""
    if not _enabled_for(ip):
        return
    start, _ = _window(time.time())
    try:
        _redis().decr(f"{KEY_PREFIX}{ip}:{start}")
    except Exception:  # noqa: BLE001
        pass

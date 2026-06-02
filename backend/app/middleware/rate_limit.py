"""
In-memory rate limiter for auth endpoints.

Limits: 5 requests per minute per IP on guarded paths.

Architecture: in-memory dict with TTL cleanup.
Interface is Redis-ready — swap _backend for a Redis adapter without
changing any callsites.
"""
import time
from collections import defaultdict
from typing import Protocol


# ── Backend protocol (Redis-ready interface) ──────────────────────────────────

class RateLimitBackend(Protocol):
    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        ...


class InMemoryRateLimitBackend:
    """
    Simple sliding-window counter backed by an in-process dict.

    Not suitable for multi-process deployments — swap for Redis in production.
    """

    def __init__(self) -> None:
        # key → list of request timestamps within the current window
        self._store: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        timestamps = self._store[key]

        # Evict expired entries
        self._store[key] = [t for t in timestamps if t > cutoff]

        if len(self._store[key]) >= limit:
            return False  # rate-limited

        self._store[key].append(now)
        return True


# Singleton backend (swap for Redis-backed impl in production)
_backend = InMemoryRateLimitBackend()


# ── FastAPI dependency ────────────────────────────────────────────────────────

_GUARDED_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/recovery/request",
}
_RATE_LIMIT = 5
_WINDOW_SECONDS = 60


def check_rate_limit(client_ip: str, path: str) -> bool:
    """
    Return True if the request is allowed.
    Call this at the top of guarded endpoint handlers.
    """
    if path not in _GUARDED_PATHS:
        return True
    key = f"rl:{path}:{client_ip}"
    return _backend.check(key, _RATE_LIMIT, _WINDOW_SECONDS)


def get_client_ip(request: "Request") -> str:  # type: ignore[name-defined]
    """Extract the real client IP, respecting X-Forwarded-For (trusted proxy)."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"

"""In-memory brute-force throttle for the login endpoint (OWASP ASVS V2.2.1).

After too many failed attempts for the same (client IP + email) pair within a
sliding window, further attempts are refused with 429 until the window clears.
A successful login resets the counter for that pair.

This is deliberately a single-process, in-memory implementation — enough to blunt
online password guessing in this MVP. A real deployment behind multiple workers
would back this with a shared store (Redis) so the limit is global.
"""
import time
from collections import defaultdict, deque

# Tunables. Five wrong guesses buys a fifteen-minute lockout for that pair.
MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60


class LoginRateLimiter:
    def __init__(self, max_failures: int = MAX_FAILURES, window: int = WINDOW_SECONDS):
        self.max_failures = max_failures
        self.window = window
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> None:
        bucket = self._failures[key]
        cutoff = now - self.window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if not bucket:
            self._failures.pop(key, None)

    def retry_after(self, key: str) -> int:
        """Seconds until the caller may try again, or 0 if not locked out."""
        now = time.monotonic()
        self._prune(key, now)
        bucket = self._failures.get(key)
        if not bucket or len(bucket) < self.max_failures:
            return 0
        # Locked out until the oldest failure in the window ages out.
        return max(1, int(bucket[0] + self.window - now))

    def is_locked(self, key: str) -> bool:
        return self.retry_after(key) > 0

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        self._prune(key, now)
        self._failures[key].append(now)

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)

    def clear(self) -> None:
        """Drop all state — used to isolate tests."""
        self._failures.clear()


login_rate_limiter = LoginRateLimiter()


class SlidingWindowCounter:
    """Counts every event per key in a sliding window and caps it.

    Unlike the login limiter (which only counts failures), this caps *all*
    calls — used to bound the billable AI endpoints.
    """

    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> None:
        bucket = self._events[key]
        cutoff = now - self.window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if not bucket:
            self._events.pop(key, None)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        self._prune(key, now)
        if len(self._events[key]) >= self.limit:
            return False
        self._events[key].append(now)
        return True

    def clear(self) -> None:
        self._events.clear()


# The AI endpoints call Claude and cost money per request. The demo login is
# public, so anyone could reach them — cap usage so no one can run up the bill:
# a per-IP burst limit and a hard global daily ceiling.
ai_per_ip_limiter = SlidingWindowCounter(limit=15, window=10 * 60)
ai_global_limiter = SlidingWindowCounter(limit=500, window=24 * 60 * 60)

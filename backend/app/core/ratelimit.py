"""In-memory sliding-window rate limiter for login brute-force protection.

Memorious per-key hit deques in a process-local dict — appropriate for the
single-process FastAPI backend; account lockout (persistent) lives in the DB
so it survives restarts and works across workers.
"""
from __future__ import annotations

import threading
import time
from collections import deque


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        """Record a hit; return False when over the per-window quota."""
        now = time.monotonic()
        with self._lock:
            q = self._hits.get(key)
            if q is None:
                q = self._hits[key] = deque()
            while q and now - q[0] > self.window_seconds:
                q.popleft()
            if len(q) >= self.max_requests:
                return False
            q.append(now)
            return True
"""Count recent failures per key (an IP address, an account) inside a sliding window.

Kept in this process's memory: enough for one server process, lost on restart, not shared
between processes. No Redis, as the build brief requires.
"""

import threading
import time
from collections import deque
from collections.abc import Callable


class FailureLimiter:
    def __init__(
        self,
        max_failures: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max = max_failures
        self._window = window_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str) -> deque[float]:
        recent = self._failures.get(key)
        if recent is None:
            return deque()
        cutoff = self._clock() - self._window
        while recent and recent[0] <= cutoff:
            recent.popleft()
        if not recent:
            del self._failures[key]
        return recent

    def is_blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._prune(key)) >= self._max

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._prune(key)
            self._failures.setdefault(key, deque()).append(self._clock())
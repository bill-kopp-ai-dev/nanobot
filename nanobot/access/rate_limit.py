"""Bounded rate limits for password and elevation attempts.

The gateway persists only timestamp counters and one-way source identifiers,
never raw client addresses. The default in-memory mode remains available for
small unit-level uses; production controllers provide a path so restarting a
gateway doesn't reset the attack budget.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Generator, TypedDict, cast

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback is thread-safe only
    fcntl = None  # type: ignore[assignment]

from nanobot.utils.helpers import _write_text_atomic  # pyright: ignore[reportPrivateUsage]

_SHORT_WINDOW_S = 60.0
_SHORT_LIMIT = 5
_MEDIUM_WINDOW_S = 15 * 60.0
_MEDIUM_LIMIT = 15
_LONG_WINDOW_S = 60 * 60.0
_LONG_LIMIT = 25
_GLOBAL_LIMIT_PER_MIN = 60
_MAX_SOURCES = 4096


@dataclass
class _Bucket:
    attempts: Deque[float] = field(default_factory=deque)


class _PersistedState(TypedDict):
    schemaVersion: int
    global_attempts: list[float]
    sources: dict[str, list[float]]


class RateLimitStore:
    def __init__(
        self,
        *,
        short_window_s: float = _SHORT_WINDOW_S,
        short_limit: int = _SHORT_LIMIT,
        medium_window_s: float = _MEDIUM_WINDOW_S,
        medium_limit: int = _MEDIUM_LIMIT,
        long_window_s: float = _LONG_WINDOW_S,
        long_limit: int = _LONG_LIMIT,
        global_per_min: int = _GLOBAL_LIMIT_PER_MIN,
        path: Path | None = None,
    ) -> None:
        self._short_window_s = short_window_s
        self._short_limit = short_limit
        self._medium_window_s = medium_window_s
        self._medium_limit = medium_limit
        self._long_window_s = long_window_s
        self._long_limit = long_limit
        self._global_per_min = global_per_min
        self._path = path
        self._buckets: dict[str, _Bucket] = {}
        self._global: Deque[float] = deque()
        self._mutex = threading.RLock()

    def check(self, source: str) -> tuple[bool, float]:
        """Return (allowed, retry_after_s), without consuming an attempt."""
        if self._path is not None:
            with self._locked_state() as state:
                now = time.time()
                self._prune_state(state, now)
                return self._check_times(self._source_times(state, source), state["global_attempts"], now)
        with self._mutex:
            now = time.monotonic()
            self._prune_global(now)
            bucket = self._buckets.setdefault(source or "unknown", _Bucket())
            self._prune(bucket, now, self._long_window_s)
            return self._check_times(list(bucket.attempts), list(self._global), now)

    def check_and_record(self, source: str) -> tuple[bool, float]:
        """Atomically check and reserve an attempt before expensive hashing."""
        if self._path is not None:
            with self._locked_state() as state:
                now = time.time()
                self._prune_state(state, now)
                attempts = self._source_times(state, source)
                allowed, retry = self._check_times(attempts, state["global_attempts"], now)
                if allowed:
                    attempts.append(now)
                    state["global_attempts"].append(now)
                return allowed, retry
        with self._mutex:
            allowed, retry = self.check(source)
            if allowed:
                self.record(source)
            return allowed, retry

    def record(self, source: str) -> None:
        """Record an attempt (retained for callers that separate check/record)."""
        if self._path is not None:
            with self._locked_state() as state:
                now = time.time()
                self._prune_state(state, now)
                self._source_times(state, source).append(now)
                state["global_attempts"].append(now)
            return
        with self._mutex:
            now = time.monotonic()
            self._buckets.setdefault(source or "unknown", _Bucket()).attempts.append(now)
            self._global.append(now)

    def clear_source(self, source: str) -> None:
        """Clear one source's failed-attempt history after successful auth."""
        if self._path is not None:
            with self._locked_state() as state:
                state["sources"].pop(self._source_key(source), None)
            return
        with self._mutex:
            self._buckets.pop(source or "unknown", None)

    def reset(self) -> None:
        if self._path is not None:
            with self._locked_state() as state:
                state["sources"].clear()
                state["global_attempts"].clear()
            return
        with self._mutex:
            self._buckets.clear()
            self._global.clear()

    def _check_times(
        self,
        attempts: list[float],
        global_attempts: list[float],
        now: float,
    ) -> tuple[bool, float]:
        if len(global_attempts) >= self._global_per_min:
            return False, max(0.0, global_attempts[0] + 60.0 - now)
        long = [t for t in attempts if now - t < self._long_window_s]
        if len(long) >= self._long_limit:
            return False, max(0.0, long[-self._long_limit] + self._long_window_s - now)
        short = [t for t in long if now - t < self._short_window_s]
        if len(short) >= self._short_limit:
            return False, max(0.0, short[-self._short_limit] + self._short_window_s - now)
        medium = [t for t in long if now - t < self._medium_window_s]
        if len(medium) >= self._medium_limit:
            return False, max(0.0, medium[-self._medium_limit] + self._medium_window_s - now)
        return True, 0.0

    @contextlib.contextmanager
    def _locked_state(self) -> Generator[_PersistedState, None, None]:
        assert self._path is not None
        with self._mutex:
            self._path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(self._path.parent, 0o700)
            lock_path = self._path.with_suffix(self._path.suffix + ".lock")
            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                if fcntl is not None:
                    fcntl.flock(fd, fcntl.LOCK_EX)
                state = self._read_state()
                yield state
                self._write_state(state)
            finally:
                if fcntl is not None:
                    with contextlib.suppress(OSError):
                        fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)

    def _read_state(self) -> _PersistedState:
        assert self._path is not None
        if not self._path.exists():
            return {"schemaVersion": 1, "global_attempts": [], "sources": {}}
        try:
            raw: object = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("invalid rate-limit state")
            value = cast(dict[str, object], raw)
            if (
                value.get("schemaVersion") != 1
                or not isinstance(value.get("global_attempts"), list)
                or not isinstance(value.get("sources"), dict)
            ):
                raise ValueError("invalid rate-limit state")
            global_times = _number_list(value["global_attempts"])
            sources_raw = cast(dict[object, object], value["sources"])
            sources: dict[str, list[float]] = {}
            for key, times in sources_raw.items():
                if not isinstance(key, str):
                    raise ValueError("invalid source identifier")
                sources[key] = _number_list(times)
            return {"schemaVersion": 1, "global_attempts": global_times, "sources": sources}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise RuntimeError("rate-limit state is unreadable") from exc

    def _write_state(self, state: _PersistedState) -> None:
        assert self._path is not None
        _write_text_atomic(self._path, json.dumps(state, separators=(",", ":")), initial_mode=0o600)
        with contextlib.suppress(OSError):
            os.chmod(self._path, 0o600)

    def _prune_state(self, state: _PersistedState, now: float) -> None:
        cutoff = now - self._long_window_s
        state["global_attempts"][:] = [
            t for t in state["global_attempts"] if now - t < 60.0
        ]
        sources = state["sources"]
        for key in list(sources):
            fresh = [t for t in sources[key] if t >= cutoff and t <= now + 60.0]
            if fresh:
                sources[key] = fresh
            else:
                del sources[key]
        if len(sources) > _MAX_SOURCES:
            oldest = sorted(sources, key=lambda key: max(sources[key]))[:len(sources) - _MAX_SOURCES]
            for key in oldest:
                del sources[key]

    def _source_times(self, state: _PersistedState, source: str) -> list[float]:
        return state["sources"].setdefault(self._source_key(source), [])

    @staticmethod
    def _source_key(source: str) -> str:
        return hashlib.sha256((source or "unknown").encode("utf-8", errors="replace")).hexdigest()

    def _prune(self, bucket: _Bucket, now: float, window_s: float) -> None:
        cutoff = now - window_s
        while bucket.attempts and bucket.attempts[0] < cutoff:
            bucket.attempts.popleft()

    def _prune_global(self, now: float) -> None:
        cutoff = now - 60.0
        while self._global and self._global[0] < cutoff:
            self._global.popleft()


def _number_list(value: object) -> list[float]:
    if not isinstance(value, list):
        raise ValueError("invalid timestamp list")
    numbers: list[float] = []
    for item in cast(list[object], value):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError("invalid timestamp")
        numbers.append(float(item))
    return numbers


__all__ = ["RateLimitStore"]

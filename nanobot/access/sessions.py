"""In-memory session store keyed by an opaque identifier.

A session is created after a successful password login. Sessions survive a
page refresh but are invalidated on gateway restart, logout, password change,
or idle/absolute expiration. They never persist to disk.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any

SESSION_COOKIE_NAME = "percival_session"
SESSION_CSRF_COOKIE = "percival_csrf"
SESSION_CSRF_HEADER = "X-Percival-CSRF"

SESSION_IDLE_TTL_S = 30 * 60          # 30 min
SESSION_ABSOLUTE_TTL_S = 12 * 60 * 60  # 12 h

_SESSION_ID_BYTES = 32
_CSRF_TOKEN_BYTES = 32
_MAX_SESSIONS = 256


@dataclass(slots=True)
class Session:
    session_id: str
    csrf_token: str
    created_at: float
    last_active: float
    absolute_expiry: float
    idle_expiry: float
    source: str
    elevation_expiry: float = 0.0
    revoked: bool = False

    def touch(self, now: float) -> None:
        self.last_active = now
        self.idle_expiry = now + SESSION_IDLE_TTL_S

    def is_valid(self, now: float) -> bool:
        if self.revoked:
            return False
        if now >= self.absolute_expiry:
            return False
        if now >= self.idle_expiry:
            return False
        return True

    def is_elevated(self, now: float) -> bool:
        if self.revoked:
            return False
        return now < self.elevation_expiry


@dataclass
class SessionStore:
    max_sessions: int = _MAX_SESSIONS
    _sessions: dict[str, Session] = field(default_factory=dict)
    _by_csrf: dict[str, str] = field(default_factory=dict)

    def create(self, source: str) -> Session:
        now = time.monotonic()
        if len(self._sessions) >= self.max_sessions:
            self._evict_expired(now)
            if len(self._sessions) >= self.max_sessions:
                self._drop_oldest_idle()
        session_id = secrets.token_urlsafe(_SESSION_ID_BYTES)
        csrf = secrets.token_urlsafe(_CSRF_TOKEN_BYTES)
        session = Session(
            session_id=session_id,
            csrf_token=csrf,
            created_at=now,
            last_active=now,
            absolute_expiry=now + SESSION_ABSOLUTE_TTL_S,
            idle_expiry=now + SESSION_IDLE_TTL_S,
            source=source,
        )
        self._sessions[session_id] = session
        self._by_csrf[csrf] = session_id
        return session

    def lookup(self, session_id: str | None) -> Session | None:
        if not session_id:
            return None
        return self._sessions.get(session_id)

    def touch(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if not session.is_valid(time.monotonic()):
            return session
        session.touch(time.monotonic())
        return session

    def revoke(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.revoked = True
        self._by_csrf.pop(session.csrf_token, None)
        self._sessions.pop(session_id, None)

    def revoke_all(self) -> None:
        for session_id in list(self._sessions):
            self.revoke(session_id)

    def csrf_for_session(self, session_id: str) -> str | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        return session.csrf_token

    def session_for_csrf(self, csrf_token: str | None) -> Session | None:
        if not csrf_token:
            return None
        session_id = self._by_csrf.get(csrf_token)
        if session_id is None:
            return None
        return self._sessions.get(session_id)

    def cleanup(self) -> None:
        self._evict_expired(time.monotonic())

    def stats(self) -> dict[str, Any]:
        return {
            "active": sum(1 for s in self._sessions.values() if not s.revoked),
            "max": self.max_sessions,
        }

    def _evict_expired(self, now: float) -> None:
        expired = [
            sid for sid, s in self._sessions.items() if not s.is_valid(now)
        ]
        for sid in expired:
            session = self._sessions.pop(sid, None)
            if session is not None:
                self._by_csrf.pop(session.csrf_token, None)

    def _drop_oldest_idle(self) -> None:
        if not self._sessions:
            return
        oldest = min(
            self._sessions.values(),
            key=lambda s: s.last_active,
        )
        self.revoke(oldest.session_id)


__all__ = [
    "SESSION_ABSOLUTE_TTL_S",
    "SESSION_COOKIE_NAME",
    "SESSION_CSRF_COOKIE",
    "SESSION_CSRF_HEADER",
    "SESSION_IDLE_TTL_S",
    "Session",
    "SessionStore",
]

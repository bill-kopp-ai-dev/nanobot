"""Per-session administrative elevation for MCP mutations.

Elevation is an additional authentication step for sensitive actions (all
twelve MCP Docker operations). The same human password is verified again to
grant a short-lived (15 min) elevation bound to the existing session; logout,
password rotation, session expiry/revocation, or restart immediately revoke
the grant.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

ELEVATION_TTL_S = 15 * 60


@dataclass(slots=True)
class ElevationGrant:
    session_id: str
    granted_at: float
    expires_at: float
    source: str

    def is_valid(self, now: float) -> bool:
        return now < self.expires_at


class ElevationStore:
    """In-memory record of currently elevated sessions."""

    def __init__(self, ttl_s: int = ELEVATION_TTL_S) -> None:
        self._ttl_s = ttl_s
        self._grants: dict[str, ElevationGrant] = {}

    def grant(self, session_id: str, source: str) -> ElevationGrant:
        now = time.monotonic()
        grant = ElevationGrant(
            session_id=session_id,
            granted_at=now,
            expires_at=now + self._ttl_s,
            source=source,
        )
        self._grants[session_id] = grant
        return grant

    def is_elevated(self, session_id: str | None) -> bool:
        if not session_id:
            return False
        grant = self._grants.get(session_id)
        if grant is None:
            return False
        if not grant.is_valid(time.monotonic()):
            self._grants.pop(session_id, None)
            return False
        return True

    def revoke(self, session_id: str) -> None:
        self._grants.pop(session_id, None)

    def revoke_all(self) -> None:
        self._grants.clear()

    def ttl_s(self) -> int:
        return self._ttl_s

    def remaining_s(self, session_id: str) -> float:
        grant = self._grants.get(session_id)
        if grant is None:
            return 0.0
        return max(0.0, grant.expires_at - time.monotonic())


__all__ = [
    "ELEVATION_TTL_S",
    "ElevationGrant",
    "ElevationStore",
]

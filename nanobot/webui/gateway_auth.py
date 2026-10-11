"""Gateway-side authentication controller.

Owns the AccessCredential, the in-memory session/elevation/rate-limit
stores, and the small set of operations the HTTP and WS layers need to call.
The broker and Docker host are not part of this surface; the broker keeps
its own unrelated token.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from loguru import logger

from nanobot.access.credential import AccessCredential
from nanobot.access.elevation import ElevationStore
from nanobot.access.errors import (
    AuthError,
    AuthThrottledError,
    AuthUnavailableError,
    ElevationRequiredError,
    SessionExpiredError,
    SessionNotFoundError,
    SetupRequiredError,
)
from nanobot.access.password import (
    PasswordPolicyError,
    PasswordRuleViolation,
    PasswordTooLongError,
    PasswordTooShortError,
    accept_password,
    validate_password_strength,
)
from nanobot.access.rate_limit import RateLimitStore
from nanobot.access.sessions import Session, SessionStore


@dataclass
class AccessController:
    credential: AccessCredential
    sessions: SessionStore
    elevation: ElevationStore
    rate_limit: RateLimitStore
    log: Any = logger

    def __post_init__(self) -> None:
        self._credential_revision = self.credential.revision()

    @classmethod
    def from_data_dir(cls, data_dir: Any, *, log: Any = logger) -> "AccessController":
        return cls(
            credential=AccessCredential(data_dir),
            sessions=SessionStore(),
            elevation=ElevationStore(),
            rate_limit=RateLimitStore(path=data_dir / "auth" / "rate-limits.json"),
            log=log,
        )

    def has_password(self) -> bool:
        return self.credential.exists()

    def is_password_usable(self) -> bool:
        return self.credential.is_usable()

    def setup(self, password: str) -> Session:
        self._sync_credential_revision()
        if self.credential.exists():
            raise SetupRequiredError("password already configured")
        self.credential.set_password(password)
        self._sync_credential_revision()
        return self.sessions.create(source="setup")

    def change_password(
        self,
        *,
        current_password: str,
        new_password: str,
    ) -> None:
        self._sync_credential_revision()
        self.credential.set_password(new_password, current_password=current_password)
        self._sync_credential_revision()

    def local_recover(self, password: str) -> None:
        """Local-recovery path used by the CLI on a trusted console."""
        self.credential.set_password(password, recover=True)
        self._sync_credential_revision()

    def login(
        self,
        password: str,
        *,
        source: str,
    ) -> Session:
        self._sync_credential_revision()
        self._consume_attempt(source)
        if not self.credential.exists():
            raise AuthError("invalid password")
        if not self.credential.verify(password):
            raise AuthError("invalid password")
        self.rate_limit.clear_source(source)
        return self.sessions.create(source=source)

    def logout(self, session_id: str) -> None:
        self.sessions.revoke(session_id)
        self.elevation.revoke(session_id)
        self._revoke_session_tokens(session_id)

    def session(self, session_id: str | None) -> Session:
        self._sync_credential_revision()
        if not session_id:
            raise SessionNotFoundError("missing session")
        session = self.sessions.lookup(session_id)
        if session is None:
            raise SessionNotFoundError("session not found")
        if not session.is_valid(time.monotonic()):
            self.sessions.revoke(session_id)
            self.elevation.revoke(session_id)
            self._revoke_session_tokens(session_id)
            raise SessionExpiredError("session expired")
        session.touch(time.monotonic())
        return session

    def session_is_valid(self, session_id: str) -> bool:
        """Check expiry without extending the idle window (for socket reaping)."""
        self._sync_credential_revision()
        session = self.sessions.lookup(session_id)
        if session is None:
            return False
        if session.is_valid(time.monotonic()):
            return True
        self.sessions.revoke(session_id)
        self.elevation.revoke(session_id)
        self._revoke_session_tokens(session_id)
        return False

    def elevate(
        self,
        *,
        password: str,
        session_id: str,
        source: str,
    ) -> float:
        self._consume_attempt(source)
        if not self.credential.exists():
            raise AuthUnavailableError("credential is not configured")
        if not self.credential.verify(password):
            raise AuthError("invalid password")
        self.rate_limit.clear_source(source)
        session = self.session(session_id)
        grant = self.elevation.grant(session.session_id, source=source)
        return max(0.0, grant.expires_at - time.monotonic())

    def require_elevation(self, session_id: str | None) -> Session:
        session = self.session(session_id)
        if not self.elevation.is_elevated(session.session_id):
            raise ElevationRequiredError("elevation required")
        return session

    def elevation_remaining_s(self, session_id: str | None) -> float:
        if not session_id:
            return 0.0
        return self.elevation.remaining_s(session_id)

    def status(self, session_id: str | None) -> dict[str, Any]:
        if not self.credential.exists():
            return {
                "configured": False,
                "authenticated": False,
                "elevated": False,
                "elevation_remaining_s": 0.0,
            }
        if not session_id:
            return {
                "configured": True,
                "authenticated": False,
                "elevated": False,
                "elevation_remaining_s": 0.0,
            }
        try:
            session = self.session(session_id)
        except AuthError:
            return {
                "configured": True,
                "authenticated": False,
                "elevated": False,
                "elevation_remaining_s": 0.0,
            }
        elevated = self.elevation.is_elevated(session.session_id)
        return {
            "configured": True,
            "authenticated": True,
            "elevated": elevated,
            "elevation_remaining_s": (
                self.elevation.remaining_s(session.session_id) if elevated else 0.0
            ),
            "session_idle_remaining_s": max(0.0, session.idle_expiry - time.monotonic()),
            "session_absolute_remaining_s": max(
                0.0, session.absolute_expiry - time.monotonic()
            ),
        }

    # -- Token coordination ------------------------------------------------

    def _revoke_session_tokens(self, session_id: str) -> None:
        """Subclass wiring revokes issued tokens; placeholder when absent."""
        revoke = getattr(self, "_token_revoke_hook", None)
        if callable(revoke):
            revoke(session_id)

    def attach_token_store(self, token_store: Any) -> None:
        self._token_revoke_hook = token_store.revoke_session_tokens
        self._token_clear_hook = token_store.clear
        token_store.session_validator = self._session_token_valid

    def attach_endpoint(self, endpoint: Any) -> None:
        self._connection_revoke_hook = endpoint.revoke_all_sessions

    def _session_token_valid(self, session_id: str) -> bool:
        try:
            self.session(session_id)
        except AuthError:
            return False
        return True

    def _sync_credential_revision(self) -> None:
        revision = self.credential.revision()
        if revision == self._credential_revision:
            return
        self._credential_revision = revision
        self.sessions.revoke_all()
        self.elevation.revoke_all()
        clear = getattr(self, "_token_clear_hook", None)
        if callable(clear):
            clear()
        revoke_connections = getattr(self, "_connection_revoke_hook", None)
        if callable(revoke_connections):
            revoke_connections()

    def refresh_credential_revision(self) -> None:
        """Observe a credential init/rotation performed by another CLI process."""
        self._sync_credential_revision()

    def _consume_attempt(self, source: str) -> None:
        allowed, retry_after = self.rate_limit.check_and_record(source)
        if not allowed:
            raise AuthThrottledError(retry_after)


__all__ = [
    "AccessController",
    "AuthError",
    "AuthThrottledError",
    "AuthUnavailableError",
    "ElevationRequiredError",
    "PasswordPolicyError",
    "PasswordRuleViolation",
    "PasswordTooLongError",
    "PasswordTooShortError",
    "Session",
    "SessionExpiredError",
    "SessionNotFoundError",
    "SetupRequiredError",
    "accept_password",
    "validate_password_strength",
]

from __future__ import annotations


class AccessError(Exception):
    """Base class for access-layer errors."""


class SetupRequiredError(AccessError):
    """Raised when an authentication action needs a configured password first."""


class AuthError(AccessError):
    """Base for authentication failures (bad password, expired session, etc)."""


class AuthThrottledError(AuthError):
    """Too many authentication attempts for the source or account."""

    def __init__(self, retry_after_s: float) -> None:
        super().__init__(f"too many attempts; retry in {retry_after_s:.0f}s")
        self.retry_after_s = float(retry_after_s)


class AuthUnavailableError(AuthError):
    """Authentication is unavailable because the verifier is missing or broken."""


class SessionNotFoundError(AuthError):
    """The presented session identifier is not recognized."""


class SessionExpiredError(AuthError):
    """The session was valid but has expired (absolute or idle)."""


class ElevationRequiredError(AuthError):
    """The action needs an elevated session; re-authenticate with the password."""


__all__ = [
    "AccessError",
    "AuthError",
    "AuthThrottledError",
    "AuthUnavailableError",
    "ElevationRequiredError",
    "SessionExpiredError",
    "SessionNotFoundError",
    "SetupRequiredError",
]

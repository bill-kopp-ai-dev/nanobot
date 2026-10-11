"""Single human password per Percival instance.

Owns the credential verifier, in-memory sessions, per-session elevation,
rate-limited authentication, and the password policy (NIST SP 800-63B-4 §3.1.1).

The broker keeps its own unrelated token; the WebUI password does not appear
in the broker path, in environment variables, or in URL parameters. Sessions
are issued after the password verifies and survive a page refresh but are
invalidated on gateway restart, password change, logout, or expiration.
"""

from __future__ import annotations

from nanobot.access.credential import (
    AccessCredential,
    AccessCredentialError,
)
from nanobot.access.elevation import (
    ELEVATION_TTL_S,
    ElevationGrant,
    ElevationStore,
)
from nanobot.access.errors import (
    AccessError,
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
    normalize_password,
    validate_password_strength,
)
from nanobot.access.rate_limit import RateLimitStore
from nanobot.access.sessions import (
    SESSION_ABSOLUTE_TTL_S,
    SESSION_COOKIE_NAME,
    SESSION_CSRF_COOKIE,
    SESSION_CSRF_HEADER,
    SESSION_IDLE_TTL_S,
    Session,
    SessionStore,
)

__all__ = [
    "AccessCredential",
    "AccessCredentialError",
    "AccessError",
    "AuthError",
    "AuthThrottledError",
    "AuthUnavailableError",
    "ELEVATION_TTL_S",
    "ElevationGrant",
    "ElevationRequiredError",
    "ElevationStore",
    "PasswordPolicyError",
    "PasswordRuleViolation",
    "PasswordTooLongError",
    "PasswordTooShortError",
    "RateLimitStore",
    "SESSION_ABSOLUTE_TTL_S",
    "SESSION_COOKIE_NAME",
    "SESSION_CSRF_COOKIE",
    "SESSION_CSRF_HEADER",
    "SESSION_IDLE_TTL_S",
    "Session",
    "SessionExpiredError",
    "SessionNotFoundError",
    "SessionStore",
    "SetupRequiredError",
    "accept_password",
    "normalize_password",
    "validate_password_strength",
]

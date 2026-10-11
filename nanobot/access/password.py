"""Password validation and normalization for the single-instance password.

Follows NIST SP 800-63B-4 §3.1.1 (consulted 2026-10-11):
- minimum length 15 characters;
- accept spaces, Unicode, manager-generated phrases;
- no mandatory character classes, no forced rotation, no composition rules;
- refuse well-known breached/contextual passwords via a small blocklist;
- normalise to Unicode NFC on both input paths.

This module does not hash or store the password; :class:`AccessCredential` does.
"""

from __future__ import annotations

import unicodedata

from nanobot.access.errors import AccessError

MIN_PASSWORD_CHARS = 15
MAX_PASSWORD_BYTES = 1024

# Compact local blocklist. Production deployments should swap this for a
# HIBP-style breach corpus; the gateway itself only enforces the rules below.
_BLOCKLIST = frozenset({
    "percival", "nanobot", "password", "passw0rd", "p@ssw0rd",
    "123456789012345", "qwertyuiopasdfg", "letmeinplease",
    "administrator", "changeme", "default", "secret",
})


class PasswordPolicyError(AccessError):
    """The password violates the active policy."""


class PasswordTooShortError(PasswordPolicyError):
    def __init__(self, length: int) -> None:
        super().__init__(f"password must be at least {MIN_PASSWORD_CHARS} characters (got {length})")
        self.length = length


class PasswordTooLongError(PasswordPolicyError):
    def __init__(self, byte_length: int) -> None:
        super().__init__(f"password exceeds {MAX_PASSWORD_BYTES} UTF-8 bytes (got {byte_length})")
        self.byte_length = byte_length


class PasswordRuleViolation(PasswordPolicyError):  # noqa: N818
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason

    def __str__(self) -> str:  # pragma: no cover - formatting only
        return self.reason


def normalize_password(value: str) -> str:
    """Normalize a password string for both store and verify paths.

    The empty string, control characters and leading/trailing whitespace are
    rejected upstream; NFC normalisation is applied here so storage and
    verification hash identical bytes.
    """
    return unicodedata.normalize("NFC", value)


def _is_too_simple(value: str) -> str | None:
    stripped = value.replace(" ", "").replace("\t", "").lower()
    if not stripped:
        return "password must contain at least one non-whitespace character"
    if stripped in _BLOCKLIST:
        return "password is too common; choose a different value"
    lower = value.lower()
    for banned in _BLOCKLIST:
        if banned in lower and len(banned) >= 8:
            return "password contains a blocked term"
    return None


def accept_password(value: str) -> str:
    """Return the normalised password when it satisfies the policy.

    Raises :class:`PasswordPolicyError` (and its subclasses) on rejection.
    """
    if any(ord(c) < 0x20 and c not in ("\t",) for c in value):
        raise PasswordPolicyError("password contains control characters")
    normalized = normalize_password(value)
    char_length = len(normalized)
    if char_length < MIN_PASSWORD_CHARS:
        raise PasswordTooShortError(char_length)
    byte_length = len(normalized.encode("utf-8"))
    if byte_length > MAX_PASSWORD_BYTES:
        raise PasswordTooLongError(byte_length)
    if (reason := _is_too_simple(normalized)) is not None:
        raise PasswordRuleViolation(reason)
    return normalized


def validate_password_strength(value: str) -> None:
    """Raise :class:`PasswordPolicyError` when the password is unacceptable."""
    accept_password(value)

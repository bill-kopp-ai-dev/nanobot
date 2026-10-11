"""Tests for the single-instance password verifier."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from nanobot.access.credential import AccessCredential, AccessCredentialError
from nanobot.access.password import (
    PasswordRuleViolation,
    PasswordTooLongError,
    PasswordTooShortError,
    accept_password,
)


def _password(length: int = 17) -> str:
    return "x" * length


def test_setup_then_verify(tmp_path: Path) -> None:
    cred = AccessCredential(tmp_path)
    assert not cred.exists()
    cred.set_password(_password(17))
    assert cred.exists()
    assert cred.is_usable()
    assert cred.verify(_password(17))
    assert not cred.verify("different-password")


def test_set_rejects_short_passwords(tmp_path: Path) -> None:
    cred = AccessCredential(tmp_path)
    with pytest.raises(PasswordTooShortError):
        cred.set_password("too-short")


def test_set_rejects_blocklist(tmp_path: Path) -> None:
    cred = AccessCredential(tmp_path)
    with pytest.raises(PasswordRuleViolation):
        cred.set_password("percival" + "x" * 12)
    with pytest.raises(PasswordRuleViolation):
        cred.set_password("Password" + "x" * 12)


def test_set_rejects_overlong(tmp_path: Path) -> None:
    cred = AccessCredential(tmp_path)
    with pytest.raises(PasswordTooLongError):
        cred.set_password("a" * 2000)


def test_set_rejects_control_chars(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        accept_password("ok-password" + "\x00extra")


def test_change_requires_current_password(tmp_path: Path) -> None:
    cred = AccessCredential(tmp_path)
    cred.set_password(_password(17))
    with pytest.raises(AccessCredentialError):
        cred.set_password(_password(18))
    cred.set_password(_password(18), current_password=_password(17))
    assert cred.verify(_password(18))
    assert not cred.verify(_password(17))


def test_recover_skips_current_password(tmp_path: Path) -> None:
    cred = AccessCredential(tmp_path)
    cred.set_password(_password(17))
    cred.set_password(_password(20), recover=True)
    assert cred.verify(_password(20))


def test_concurrent_writers_use_file_lock(tmp_path: Path) -> None:
    cred = AccessCredential(tmp_path)
    cred.set_password(_password(17))
    # Simulate concurrent init by manually moving the file and recreating it.
    cred.path.unlink()
    cred.set_password(_password(20), recover=True)
    assert cred.verify(_password(20))


def test_corrupted_verifier_reports_unusable(tmp_path: Path) -> None:
    cred = AccessCredential(tmp_path)
    cred.set_password(_password(17))
    cred.path.write_text("not-json", encoding="utf-8")
    os.chmod(cred.path, 0o600)
    assert cred.exists()
    assert not cred.is_usable()
    assert not cred.verify(_password(17))

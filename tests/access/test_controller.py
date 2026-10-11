"""Tests for the in-memory session and elevation stores."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from nanobot.access.credential import AccessCredential
from nanobot.access.elevation import ELEVATION_TTL_S, ElevationStore
from nanobot.access.errors import (
    AuthError,
    ElevationRequiredError,
    SessionExpiredError,
    SessionNotFoundError,
)
from nanobot.access.sessions import (
    SESSION_ABSOLUTE_TTL_S,
    SESSION_IDLE_TTL_S,
    SessionStore,
)
from nanobot.webui.gateway_auth import AccessController


def _password() -> str:
    return "x" * 17


def _controller(tmp_path: Path) -> AccessController:
    return AccessController.from_data_dir(tmp_path)


def test_setup_then_login(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    with pytest.raises(AuthError):
        controller.login(_password(), source="local")
    controller.setup(_password())
    session = controller.login(_password(), source="local")
    assert session.session_id
    assert session.csrf_token


def test_invalid_password_raises(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.setup(_password())
    with pytest.raises(AuthError):
        controller.login("different-password!", source="local")


def test_logout_revokes_session_and_elevation(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.setup(_password())
    session = controller.login(_password(), source="local")
    controller.elevate(
        password=_password(),
        session_id=session.session_id,
        source="local",
    )
    assert controller.elevation.is_elevated(session.session_id)
    controller.logout(session.session_id)
    with pytest.raises((SessionNotFoundError, SessionExpiredError)):
        controller.session(session.session_id)
    assert not controller.elevation.is_elevated(session.session_id)


def test_change_password_revokes_sessions(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.setup(_password())
    session = controller.login(_password(), source="local")
    controller.change_password(
        current_password=_password(),
        new_password="y" * 18,
    )
    with pytest.raises((SessionNotFoundError, SessionExpiredError)):
        controller.session(session.session_id)
    controller.login("y" * 18, source="local")
    assert controller.credential.verify("y" * 18)


def test_elevation_requires_password(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.setup(_password())
    session = controller.login(_password(), source="local")
    with pytest.raises(AuthError):
        controller.elevate(
            password="wrong",
            session_id=session.session_id,
            source="local",
        )
    assert not controller.elevation.is_elevated(session.session_id)


def test_require_elevation_after_grant(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.setup(_password())
    session = controller.login(_password(), source="local")
    with pytest.raises(ElevationRequiredError):
        controller.require_elevation(session.session_id)
    controller.elevate(
        password=_password(),
        session_id=session.session_id,
        source="local",
    )
    controller.require_elevation(session.session_id)


def test_session_idle_expiry(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.setup(_password())
    session = controller.login(_password(), source="local")
    session.idle_expiry = time.monotonic() - 1.0
    with pytest.raises(SessionExpiredError):
        controller.session(session.session_id)


def test_status_reflects_elevation(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.setup(_password())
    session = controller.login(_password(), source="local")
    status = controller.status(session.session_id)
    assert status["authenticated"] is True
    assert status["elevated"] is False
    controller.elevate(
        password=_password(),
        session_id=session.session_id,
        source="local",
    )
    status = controller.status(session.session_id)
    assert status["elevated"] is True
    assert status["elevation_remaining_s"] > 0


def test_local_recover_overwrites_password(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.setup(_password())
    controller.local_recover("z" * 19)
    assert controller.credential.verify("z" * 19)


def test_out_of_process_password_rotation_revokes_session_tokens(tmp_path: Path) -> None:
    from nanobot.access.errors import SessionNotFoundError
    from nanobot.webui.gateway_tokens import GatewayTokenStore

    controller = _controller(tmp_path)
    controller.setup(_password())
    session = controller.login(_password(), source="local")
    tokens = GatewayTokenStore()
    controller.attach_token_store(tokens)
    token = tokens.issue_api_token(300, session_id=session.session_id)
    assert token in tokens.api_tokens

    # Simulate `nanobot auth change` running in a separate CLI process.
    AccessCredential(tmp_path).set_password("z" * 19, recover=True)

    with pytest.raises(SessionNotFoundError):
        controller.session(session.session_id)
    assert not tokens.api_tokens
    assert not tokens.issued_tokens


def test_rate_limit_throttles_repeated_logins(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.setup(_password())
    for _ in range(5):
        with pytest.raises(AuthError):
            controller.login("wrong", source="local")
    from nanobot.access.errors import AuthThrottledError

    with pytest.raises(AuthThrottledError):
        controller.login("wrong", source="local")


def test_session_absolute_ttl_present() -> None:
    store = SessionStore()
    s = store.create("local")
    assert s.absolute_expiry - s.created_at == SESSION_ABSOLUTE_TTL_S
    assert s.idle_expiry - s.created_at == SESSION_IDLE_TTL_S


def test_elevation_ttl_default() -> None:
    store = ElevationStore()
    grant = store.grant("s", "local")
    assert grant.expires_at - grant.granted_at == ELEVATION_TTL_S

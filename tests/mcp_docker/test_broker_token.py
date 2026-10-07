"""Broker token file permission checks."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from nanobot.mcp_docker.client import BrokerClient, BrokerUnavailableError


def _write_token(path: Path, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text("t" * 64)
    os.chmod(path, mode)


@pytest.mark.parametrize("mode", [0o600, 0o640])
def test_broker_client_accepts_safe_token_modes(tmp_path: Path, mode: int) -> None:
    token_path = tmp_path / "broker-token"
    _write_token(token_path, mode=mode)
    os.chmod(token_path.parent, 0o700)
    # Group-readable tokens must be owned by the dedicated broker-token group.
    user_gid = os.getgid()
    if mode & 0o040:
        os.environ["PERCIVAL_BROKER_TOKEN_GID"] = str(user_gid)
        token_path.chmod(mode)
    client = BrokerClient(token_path)
    assert client.token() == "t" * 64


@pytest.mark.parametrize(
    "mode",
    [
        0o604,  # others-readable
        0o620,  # group-writable
        0o624,  # group-writable and others-readable
        0o660,  # group-writable
        0o666,  # group-writable and others-writable
        0o040,  # group-readable but owner has no access (suspect)
        0o644,  # others-readable
    ],
)
def test_broker_client_rejects_unsafe_token_modes(tmp_path: Path, mode: int) -> None:
    token_path = tmp_path / "broker-token"
    _write_token(token_path, mode=mode)
    client = BrokerClient(token_path)
    with pytest.raises(BrokerUnavailableError):
        client.token()


def test_broker_client_rejects_short_or_missing_token(tmp_path: Path) -> None:
    token_path = tmp_path / "broker-token"
    _write_token(token_path, mode=0o600)
    token_path.write_text("short")
    client = BrokerClient(token_path)
    with pytest.raises(BrokerUnavailableError):
        client.token()

    missing = tmp_path / "missing-token"
    client = BrokerClient(missing)
    with pytest.raises(BrokerUnavailableError):
        client.token()

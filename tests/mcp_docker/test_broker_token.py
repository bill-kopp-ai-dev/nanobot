"""Broker token file permission checks."""

from __future__ import annotations

import io
import json
import os
import urllib.error
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nanobot.cli.mcp_docker_f1 import app
from nanobot.mcp_docker.client import BrokerClient, BrokerRejectedError, BrokerUnavailableError


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


def test_group_mismatch_is_reported_before_network_attempt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    token_path = tmp_path / "broker-token"
    _write_token(token_path, mode=0o640)
    monkeypatch.setenv("PERCIVAL_BROKER_TOKEN_GID", str(os.getgid() + 1))
    monkeypatch.setattr("urllib.request.build_opener", lambda *_args: pytest.fail("network contacted"))
    with pytest.raises(BrokerUnavailableError) as failure:
        BrokerClient(token_path).action("health", "broker", {})
    assert failure.value.reason == "token-permissions"


def test_missing_broker_is_transport_failure_after_valid_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    token_path = tmp_path / "broker-token"
    _write_token(token_path, mode=0o600)

    class OfflineOpener:
        def open(self, *_args: object, **_kwargs: object) -> object:
            raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.build_opener", lambda *_args: OfflineOpener())
    with pytest.raises(BrokerUnavailableError) as failure:
        BrokerClient(token_path).action("health", "broker", {})
    assert failure.value.reason == "transport"
    assert "connection refused" not in str(failure.value)


def test_doctor_probes_health_without_modifying_instance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.json"
    token_path = tmp_path / "mcp-docker" / "broker-token"
    _write_token(token_path, mode=0o600)
    calls: list[tuple[str, str, dict]] = []

    def health(_client: BrokerClient, operation: str, server_id: str, data: dict) -> dict:
        calls.append((operation, server_id, data))
        return {"ready": True}

    monkeypatch.setattr(BrokerClient, "action", health)
    result = CliRunner().invoke(app, ["doctor", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "broker ready" in result.output
    assert calls == [("health", "broker", {})]
    assert not config_path.exists()


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [(400, BrokerRejectedError), (409, BrokerRejectedError), (503, BrokerUnavailableError)],
)
def test_broker_client_distinguishes_rejection_from_unavailability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    expected_error: type[Exception],
) -> None:
    token_path = tmp_path / "broker-token"
    _write_token(token_path, mode=0o600)
    error = urllib.error.HTTPError(
        "http://127.0.0.1:18081/v1/reconcile",
        status,
        "broker response",
        None,
        io.BytesIO(json.dumps({"error": "state rejected"}).encode()),
    )

    class RejectingOpener:
        def open(self, *_args: object, **_kwargs: object) -> object:
            raise error

    monkeypatch.setattr("urllib.request.build_opener", lambda *_args, **_kwargs: RejectingOpener())
    with pytest.raises(expected_error) as caught:
        BrokerClient(token_path).action("reconcile", "weather", {})
    if isinstance(caught.value, BrokerRejectedError):
        assert caught.value.status_code == status

    missing = tmp_path / "missing-token"
    client = BrokerClient(missing)
    with pytest.raises(BrokerUnavailableError):
        client.token()

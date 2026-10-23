"""Readiness must exercise the authenticated HTTP boundary, not an open socket."""

import http.server
import threading
import urllib.error
from pathlib import Path

import pytest

from nanobot.mcp_docker import broker
from nanobot.mcp_docker.probe import check


def test_probe_authenticates_and_reports_host_policy_failure(tmp_path, monkeypatch):
    token = tmp_path / "token"
    token.write_text("a" * 64)
    token.chmod(0o640)
    monkeypatch.setenv("PERCIVAL_BROKER_TOKEN_FILE", str(token))
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setattr(broker, "ready", lambda: None)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), broker.Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        port = server.server_port
        check(token, port=port)
        wrong = tmp_path / "wrong"
        wrong.write_text("b" * 64)
        wrong.chmod(0o600)
        with pytest.raises(urllib.error.HTTPError) as denied:
            check(wrong, port=port)
        assert denied.value.code == 401

        def unavailable():
            raise broker.BrokerError("incompatible host", 503)

        monkeypatch.setattr(broker, "ready", unavailable)
        with pytest.raises(urllib.error.HTTPError) as not_ready:
            check(token, port=port)
        assert not_ready.value.code == 503
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def test_probe_refuses_world_readable_token(tmp_path: Path):
    token = tmp_path / "token"
    token.write_text("a" * 64)
    token.chmod(0o644)
    with pytest.raises(ValueError, match="permissions"):
        check(token)

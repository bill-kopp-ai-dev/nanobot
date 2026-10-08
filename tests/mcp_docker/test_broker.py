from __future__ import annotations

import pytest

from nanobot.mcp_docker import broker


def test_container_lookup_distinguishes_absent_from_engine_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "docker", lambda *_args: (_ for _ in ()).throw(broker.BrokerError("Docker object not found", 404)))
    assert broker._inspect("weather") is None

    def unavailable(*_args: str) -> str:
        raise broker.BrokerError("Docker operation failed (1)", 503)

    monkeypatch.setattr(broker, "docker", unavailable)
    with pytest.raises(broker.BrokerError) as failure:
        broker._inspect("weather")
    assert failure.value.status == 503


def test_actions_check_readiness_and_exclusion_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def ready() -> object:
        calls.append("ready")
        return object()

    monkeypatch.setattr(broker, "ready", ready)
    with pytest.raises(broker.BrokerError) as failure:
        broker.action("exclude", "weather", {"expected_confirmation": "wrong"})
    assert calls == ["ready"]
    assert failure.value.status == 400


def test_observe_is_read_only_and_reports_docker_and_mcp_separately(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    source = {"type": "local-image", "reference": "sha256:" + "a" * 64}
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "image_reference", lambda _source: calls.append("image"))
    monkeypatch.setattr(broker, "_inspect", lambda _server: {"State": {"Running": True}})
    monkeypatch.setattr(broker, "_discover", lambda _server: ["forecast"])

    result = broker.action("observe", "weather", {"source": source})

    assert result == {
        "dockerObservation": "running",
        "mcpConnectivity": "connected",
        "tools": ["forecast"],
    }
    assert calls == ["image"]


def test_observe_reports_missing_image_without_claiming_container_or_mcp_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())

    def missing(_source: object) -> str:
        raise broker.ImageMissingError()

    monkeypatch.setattr(broker, "image_reference", missing)
    result = broker.action("observe", "weather", {
        "source": {"type": "local-image", "reference": "sha256:" + "a" * 64},
    })
    assert result == {"dockerObservation": "image-missing", "mcpConnectivity": "unknown", "tools": []}


def test_image_reference_translates_404_into_typed_image_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "docker", lambda *_args: (_ for _ in ()).throw(broker.BrokerError("Docker object not found", 404)))
    with pytest.raises(broker.ImageMissingError):
        broker.image_reference(broker.DockerImageSource.model_validate({
            "type": "local-image", "reference": "sha256:" + "a" * 64,
        }))


def test_observe_rejects_unknown_server_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    with pytest.raises(broker.BrokerError) as failure:
        broker.action("observe", "UPPER", {"source": {
            "type": "local-image", "reference": "sha256:" + "a" * 64,
        }})
    assert failure.value.status == 400


def test_observe_rejects_unexpected_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    with pytest.raises(broker.BrokerError) as failure:
        broker.action("observe", "weather", {"source": {
            "type": "local-image", "reference": "sha256:" + "a" * 64,
        }, "tool": "forecast"})
    assert failure.value.status == 400


def test_observe_rejects_invalid_source_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    with pytest.raises(broker.BrokerError) as failure:
        broker.action("observe", "weather", {})
    assert failure.value.status == 400


def test_observe_reports_disconnected_when_container_is_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "image_reference", lambda _source: None)
    monkeypatch.setattr(broker, "_inspect", lambda _server: {"State": {"Running": False}})

    result = broker.action("observe", "weather", {"source": {
        "type": "local-image", "reference": "sha256:" + "a" * 64,
    }})
    assert result == {"dockerObservation": "stopped", "mcpConnectivity": "disconnected", "tools": []}


def test_observe_reports_container_missing_when_inspect_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "image_reference", lambda _source: None)
    monkeypatch.setattr(broker, "_inspect", lambda _server: None)

    result = broker.action("observe", "weather", {"source": {
        "type": "local-image", "reference": "sha256:" + "a" * 64,
    }})
    assert result == {"dockerObservation": "container-missing", "mcpConnectivity": "unknown", "tools": []}


def test_observe_reports_disconnected_when_discover_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "image_reference", lambda _source: None)
    monkeypatch.setattr(broker, "_inspect", lambda _server: {"State": {"Running": True}})

    def fail_discover(_server: str) -> list[str]:
        raise broker.BrokerError("MCP tools/list returned no valid tools", 503)

    monkeypatch.setattr(broker, "_discover", fail_discover)
    result = broker.action("observe", "weather", {"source": {
        "type": "local-image", "reference": "sha256:" + "a" * 64,
    }})
    assert result == {"dockerObservation": "running", "mcpConnectivity": "disconnected", "tools": []}

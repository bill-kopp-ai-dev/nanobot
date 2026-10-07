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

from __future__ import annotations

import uuid

import pytest

from nanobot.mcp_docker import broker


def test_docker_client_29_can_target_engine27_but_engine29_is_fixture_only() -> None:
    assert broker._supported_docker_versions("29.2.0|27.5.1", allow_engine29=False)
    assert not broker._supported_docker_versions("29.2.0|29.7.2", allow_engine29=False)
    assert broker._supported_docker_versions("29.2.0|29.7.2", allow_engine29=True)


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


def test_authenticated_health_only_checks_broker_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(broker, "ready", lambda: calls.append("ready"))
    monkeypatch.setattr(broker, "_STORE", {})
    assert broker.action("health", "broker", {}) == {"ready": True, "minimumMountsSupported": True, "supportedNetworks": ["none", "bridge"]}
    assert calls == ["ready"]
    assert broker._STORE == {}


def test_update_same_image_rejects_before_removing_container(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "_STORE", {})
    source = {"type": "local-image", "reference": "sha256:" + "a" * 64}
    broker.action("hydrate", "weather", {"source": source, "configuration": {},
                                          "active": True, "tools_disabled": [], "tools": ["forecast"]})
    monkeypatch.setattr(broker, "_remove", lambda _server: pytest.fail("unchanged image removed container"))
    with pytest.raises(broker.BrokerError, match="unchanged"):
        broker.action("update-image", "weather", {"source": source})


def test_minimum_access_spawn_checks_effective_binds(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoBinds:
        def docker_args(self, mounts: list[str] | None) -> list[str]:
            assert mounts == []
            return []

    monkeypatch.setattr(broker, "ready", lambda: NoBinds())
    monkeypatch.setattr(broker, "image_reference", lambda _source: "sha256:" + "a" * 64)
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(broker, "docker", lambda *args: calls.append(args))
    monkeypatch.setattr(broker, "_running", lambda _server: True)
    inspected = {"HostConfig": {"NetworkMode": "none"}, "Mounts": []}
    monkeypatch.setattr(broker, "_inspect", lambda _server: inspected)
    server = broker.ManagedServer("weather", broker.DockerImageSource(
        type="local-image", reference="sha256:" + "a" * 64), broker.DockerHostConfig(mounts=[]))
    broker._spawn(server)
    assert not any("--mount" in args for args in calls)
    inspected["Mounts"] = [{"Type": "bind", "Destination": "/host"}]
    with pytest.raises(broker.BrokerError, match="unexpected binds"):
        broker._spawn(server)


def test_recovery_rebuilds_active_container_or_preserves_persistent_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "_STORE", {})
    removals: list[str] = []
    spawns: list[str] = []
    monkeypatch.setattr(broker, "_inspect", lambda _server: None)
    monkeypatch.setattr(broker, "_remove", lambda server_id: removals.append(server_id))
    monkeypatch.setattr(broker, "_spawn", lambda server: spawns.append(server.server_id))
    monkeypatch.setattr(broker, "_discover", lambda _server: ["forecast"])
    source = {"type": "local-image", "reference": "sha256:" + "a" * 64}

    stopped = broker.action("recover", "weather", {
        "source": source, "configuration": {"persistent": True}, "active": True,
        "tools_disabled": [], "running": False,
    })
    running = broker.action("recover", "osm", {
        "source": source, "configuration": {}, "active": True,
        "tools_disabled": [], "running": True,
    })

    assert stopped == {"running": False, "tools": []}
    assert running == {"running": False, "tools": ["forecast"]}
    assert removals == ["weather", "osm"]
    assert spawns == ["osm"]


def test_reconcile_starts_owned_stopped_container_without_replacing_it(monkeypatch: pytest.MonkeyPatch) -> None:
    image = "sha256:" + "a" * 64
    running = False
    calls: list[tuple[str, ...]] = []

    class NoBinds:
        def docker_args(self, mounts: list[str] | None) -> list[str]:
            assert mounts == []
            return []

    def docker(*args: str) -> str:
        nonlocal running
        calls.append(args)
        if args[:2] == ("image", "inspect"):
            return image
        if args == ("start", "percival-mcp-weather"):
            running = True
        return ""

    def inspect(_server_id: str) -> dict:
        return {
            "Image": image, "State": {"Running": running},
            "Config": {"Labels": {"percival.mcp-docker.server-id": "weather",
                                  "percival.mcp-docker.owner": "percival",
                                  "percival.mcp-docker.managed-by": "percival-broker"},
                       "Env": ["TEST=value"]},
            "HostConfig": {"NetworkMode": "none", "Mounts": None, "Tmpfs": None,
                           "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges"]},
        }

    monkeypatch.setattr(broker, "ready", lambda: NoBinds())
    monkeypatch.setattr(broker, "_STORE", {})
    monkeypatch.setattr(broker, "_inspect", inspect)
    monkeypatch.setattr(broker, "docker", docker)
    monkeypatch.setattr(broker, "_discover", lambda _server: ["forecast"])
    payload = {"source": {"type": "local-image", "reference": image},
               "configuration": {"persistent": True, "mounts": [],
                                 "env": {"TEST": {"kind": "plain", "value": "value"}}},
               "active": True, "tools_disabled": []}

    assert broker.action("reconcile", "weather", payload) == {"running": True, "tools": ["forecast"]}
    assert broker.action("reconcile", "weather", payload) == {"running": True, "tools": ["forecast"]}
    assert calls.count(("start", "percival-mcp-weather")) == 1
    assert not any(args[0] in {"rm", "run"} for args in calls)


@pytest.mark.parametrize("drift", ["image", "network", "mounts", "covers", "labels", "env", "capabilities"])
def test_reconcile_rejects_stopped_container_with_configuration_drift(
    monkeypatch: pytest.MonkeyPatch, drift: str,
) -> None:
    image = "sha256:" + "a" * 64
    container = {
        "Image": image, "State": {"Running": False},
        "Config": {"Labels": {"percival.mcp-docker.server-id": "weather",
                              "percival.mcp-docker.owner": "percival",
                              "percival.mcp-docker.managed-by": "percival-broker"},
                   "Env": ["TEST=value"]},
        "HostConfig": {"NetworkMode": "none", "Mounts": [], "Tmpfs": {},
                       "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges"]},
    }
    if drift == "image":
        container["Image"] = "sha256:" + "b" * 64
    elif drift == "network":
        container["HostConfig"]["NetworkMode"] = "bridge"
    elif drift == "mounts":
        container["HostConfig"]["Mounts"] = [{"Type": "bind", "Source": "/", "Target": "/host"}]
    elif drift == "covers":
        container["HostConfig"]["Tmpfs"] = {"/host/run": "rw,noexec,nosuid,nodev,mode=0700"}
    elif drift == "labels":
        container["Config"]["Labels"]["percival.mcp-docker.owner"] = "other"
    elif drift == "capabilities":
        container["HostConfig"]["CapDrop"] = []
    else:
        container["Config"]["Env"] = ["TEST=old"]
    class NoBinds:
        def docker_args(self, _mounts: list[str] | None) -> list[str]:
            return []

    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(broker, "ready", lambda: NoBinds())
    monkeypatch.setattr(broker, "_STORE", {})
    monkeypatch.setattr(broker, "_inspect", lambda _server: container)
    monkeypatch.setattr(broker, "docker", lambda *args: calls.append(args) or image)
    with pytest.raises(broker.BrokerError):
        broker.action("reconcile", "weather", {
            "source": {"type": "local-image", "reference": image},
            "configuration": {"mounts": [], "env": {"TEST": {"kind": "plain", "value": "value"}}},
            "active": True, "tools_disabled": [],
        })
    assert not any(args[0] in {"start", "rm", "run"} for args in calls)


def test_reconcile_stopped_container_verifies_bind_and_cover_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    image = "sha256:" + "a" * 64
    running = False
    bind = "type=bind,src=/srv/data,dst=/host/srv/data,bind-recursive=disabled"
    cover = "/host/srv/data/private:rw,noexec,nosuid,nodev,mode=0700"

    class CoveredBinds:
        def docker_args(self, mounts: list[str] | None) -> list[str]:
            assert mounts == ["/srv/data"]
            return ["--mount", bind, "--tmpfs", cover]

    container = {
        "Image": image, "State": {"Running": False},
        "Config": {"Labels": {"percival.mcp-docker.server-id": "weather",
                              "percival.mcp-docker.owner": "percival",
                              "percival.mcp-docker.managed-by": "percival-broker"}, "Env": []},
        "HostConfig": {"NetworkMode": "none", "CapDrop": ["ALL"],
                       "SecurityOpt": ["no-new-privileges"],
                       "Mounts": [{"Type": "bind", "Source": "/srv/data", "Target": "/host/srv/data",
                                   "BindOptions": {"NonRecursive": True}}],
                       "Tmpfs": {"/host/srv/data/private": cover.split(":", 1)[1]}},
    }

    def docker(*args: str) -> str:
        nonlocal running
        if args[:2] == ("image", "inspect"):
            return image
        assert args == ("start", "percival-mcp-weather")
        running = True
        container["State"]["Running"] = True
        return ""

    monkeypatch.setattr(broker, "_STORE", {})
    monkeypatch.setattr(broker, "ready", lambda: CoveredBinds())
    monkeypatch.setattr(broker, "_inspect", lambda _server: container)
    monkeypatch.setattr(broker, "docker", docker)
    monkeypatch.setattr(broker, "_discover", lambda _server: ["forecast"])

    result = broker.action("reconcile", "weather", {
        "source": {"type": "local-image", "reference": image},
        "configuration": {"mounts": ["/srv/data"]}, "active": True, "tools_disabled": [],
    })
    assert running and result == {"running": True, "tools": ["forecast"]}


def test_start_rehydrates_broker_state_after_process_restart(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "_STORE", {})
    running = False
    docker_calls: list[tuple[str, ...]] = []

    monkeypatch.setattr(broker, "_inspect", lambda _server: {"State": {"Running": running}})
    monkeypatch.setattr(broker, "_running", lambda _server: running)

    def docker(*args: str) -> str:
        nonlocal running
        docker_calls.append(args)
        if args[:2] == ("start", "percival-mcp-weather"):
            running = True
        return ""

    monkeypatch.setattr(broker, "docker", docker)
    monkeypatch.setattr(broker, "_discover", lambda _server: ["forecast"])
    state = {
        "source": {"type": "local-image", "reference": "sha256:" + "a" * 64},
        "configuration": {"persistent": True},
        "active": True,
        "tools_disabled": [],
        "tools": ["forecast"],
    }
    assert broker.action("status", "weather", {}) == {"registered": False}
    broker.action("hydrate", "weather", state)
    assert broker.action("status", "weather", {}) == {"registered": True}
    result = broker.action("start", "weather", {})

    assert result == {"running": True, "tools": ["forecast"]}
    assert docker_calls == [("start", "percival-mcp-weather")]
    assert broker._STORE["weather"].host.persistent is True


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
        "effectiveConfiguration": {"network": "unknown", "mounts": []},
    }
    assert calls == ["image"]


def test_observe_reports_effective_mount_targets_without_host_source_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "image_reference", lambda _source: None)
    monkeypatch.setattr(broker, "_inspect", lambda _server: {
        "State": {"Running": True},
        "HostConfig": {"NetworkMode": "none"},
        "Mounts": [
            {"Type": "bind", "Source": "/host/secrets", "Destination": "/host/srv/data", "RW": True},
            {"Type": "tmpfs", "Source": "", "Destination": "/host/var/lib/docker", "RW": True},
        ],
    })
    monkeypatch.setattr(broker, "_discover", lambda _server: ["forecast"])

    result = broker.action("observe", "weather", {"source": {
        "type": "local-image", "reference": "sha256:" + "a" * 64,
    }})

    assert result["effectiveConfiguration"] == {
        "network": "none",
        "mounts": [
            {"type": "bind", "destination": "/host/srv/data", "readWrite": True},
            {"type": "tmpfs", "destination": "/host/var/lib/docker", "readWrite": True},
        ],
    }
    assert "/host/secrets" not in str(result)


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
    assert result == {"dockerObservation": "stopped", "mcpConnectivity": "disconnected", "tools": [],
                      "effectiveConfiguration": {"network": "unknown", "mounts": []}}


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
    assert result == {"dockerObservation": "running", "mcpConnectivity": "disconnected", "tools": [],
                      "effectiveConfiguration": {"network": "unknown", "mounts": []}}


def test_observe_returns_network_and_mounts_even_when_inspect_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inspect output that lacks HostConfig/Mounts must not crash and must
    report "unknown" instead of raising inside the broker."""
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "image_reference", lambda _source: None)
    monkeypatch.setattr(broker, "_inspect", lambda _server: {"State": {"Running": True}})
    monkeypatch.setattr(broker, "_discover", lambda _server: ["forecast"])

    result = broker.action("observe", "weather", {"source": {
        "type": "local-image", "reference": "sha256:" + "a" * 64,
    }})
    assert result["effectiveConfiguration"] == {"network": "unknown", "mounts": []}


def test_observe_reports_bridge_network_when_container_uses_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(broker, "ready", lambda: object())
    monkeypatch.setattr(broker, "image_reference", lambda _source: None)
    monkeypatch.setattr(broker, "_inspect", lambda _server: {
        "State": {"Running": True},
        "HostConfig": {"NetworkMode": "bridge"},
        "Mounts": [
            {"Type": "bind", "Source": "/host", "Destination": "/host", "RW": True},
        ],
    })
    monkeypatch.setattr(broker, "_discover", lambda _server: ["forecast"])

    result = broker.action("observe", "weather", {"source": {
        "type": "local-image", "reference": "sha256:" + "a" * 64,
    }})
    assert result["effectiveConfiguration"] == {
        "network": "bridge",
        "mounts": [
            {"type": "bind", "destination": "/host", "readWrite": True},
        ],
    }


def test_spawn_uses_configured_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """The ``--network=`` flag on the spawn ``docker run`` must come from
    ``server.host.network`` so servers that need external APIs can opt into
    ``bridge`` while the default stays ``none``."""
    invoked: list[list[str]] = []

    class _EmptyPolicy:
        def docker_args(self, _mounts: list[str] | None) -> list[str]:
            return []

    monkeypatch.setattr(broker, "ready", lambda: _EmptyPolicy())

    def fake_docker(*args: str) -> str:
        invoked.append(list(args))
        return ""

    monkeypatch.setattr(broker, "docker", fake_docker)
    monkeypatch.setattr(broker, "image_reference", lambda _source: "sha256:" + "a" * 64)
    monkeypatch.setattr(broker, "_running", lambda _server: True)
    monkeypatch.setattr(broker, "_inspect", lambda _server: {
        "HostConfig": {"NetworkMode": "bridge", "Tmpfs": {}},
        "Mounts": [],
    })

    source = broker.DockerImageSource.model_validate({
        "type": "local-image", "reference": "sha256:" + "a" * 64,
    })
    host = broker.DockerHostConfig(network="bridge")
    broker._spawn(broker.ManagedServer("agentmail", source, host))

    assert invoked, "docker run was not invoked"
    run_args = invoked[0]
    network_index = run_args.index("--network=bridge")
    # The run args must follow the established security ordering: image label
    # precedes network so a misbehaving image cannot rebind the network.
    label_index = run_args.index("percival.mcp-docker.server-id=agentmail")
    assert run_args[label_index - 1] == "--label"
    assert "percival.mcp-docker.owner=percival" in run_args
    assert "percival.mcp-docker.managed-by=percival-broker" in run_args
    instance_index = next(i for i, value in enumerate(run_args) if value.startswith("percival.mcp-docker.instance-id="))
    assert run_args[instance_index - 1] == "--label"
    instance_id = run_args[instance_index].split("=", 1)[1]
    assert str(uuid.UUID(instance_id)) == instance_id
    assert label_index < network_index
    assert "--cap-drop=ALL" in run_args
    assert "--security-opt=no-new-privileges" in run_args


def test_spawn_rejects_network_policy_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the daemon schedules the container with a different ``NetworkMode``
    than ``server.host.network``, the broker must fail closed rather than
    trust the config alone."""

    class _EmptyPolicy:
        def docker_args(self, _mounts: list[str] | None) -> list[str]:
            return []

    monkeypatch.setattr(broker, "ready", lambda: _EmptyPolicy())
    monkeypatch.setattr(broker, "docker", lambda *_args: "")
    monkeypatch.setattr(broker, "image_reference", lambda _source: "sha256:" + "a" * 64)
    monkeypatch.setattr(broker, "_running", lambda _server: True)
    monkeypatch.setattr(broker, "_inspect", lambda _server: {
        "HostConfig": {"NetworkMode": "none", "Tmpfs": {}},
        "Mounts": [],
    })

    source = broker.DockerImageSource.model_validate({
        "type": "local-image", "reference": "sha256:" + "a" * 64,
    })
    host = broker.DockerHostConfig(network="bridge")
    with pytest.raises(broker.BrokerError) as failure:
        broker._spawn(broker.ManagedServer("agentmail", source, host))
    assert failure.value.status == 409
    assert "network policy mismatch" in failure.value.args[0]


def test_docker_host_config_accepts_bridge_and_default_still_none() -> None:
    """The contract must accept ``bridge`` as an explicit opt-in and default
    to ``none`` so a missing field is always safe."""
    assert broker.DockerHostConfig().network == "none"
    assert broker.DockerHostConfig(network="none").network == "none"
    assert broker.DockerHostConfig(network="bridge").network == "bridge"
    with pytest.raises(ValueError):
        broker.DockerHostConfig(network="host")

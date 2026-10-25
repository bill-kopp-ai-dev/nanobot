"""Focused regression tests for the F4 Compose contract checker."""

from scripts.check_compose_contract import ServiceSpec, _is_secret_name, check_service


def valid_stdio() -> dict[str, object]:
    return {
        "init": True,
        "restart": "no",
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "read_only": True,
        "user": "1000:1000",
        "stdin_open": True,
        "environment": {"MCP_TRANSPORT": "stdio"},
        "volumes": [],
    }


def valid_http() -> dict[str, object]:
    return {
        "init": True,
        "restart": "unless-stopped",
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "read_only": True,
        "user": "1000:1000",
        "healthcheck": {"test": ["CMD", "true"]},
        "environment": {"MCP_TRANSPORT": "http"},
        "ports": [{"host_ip": "127.0.0.1", "published": "8080", "target": 8080}],
        "volumes": [],
    }


def findings_for(service: dict[str, object], *, expected: ServiceSpec) -> list[str]:
    return [
        finding.rule
        for finding in check_service(
            service="fixture",
            rendered=service,
            source={},
            expected=expected,
            env_prefixes=("MCP_FIXTURE_",),
            shared_env=("MCP_TRANSPORT",),
            env_file_keys=set(),
        )
    ]


def test_stdio_rejects_tty_ports_and_http_healthcheck() -> None:
    service = valid_stdio()
    service.update(
        {
            "tty": True,
            "ports": [{"host_ip": "127.0.0.1", "published": "8080", "target": 8080}],
            "healthcheck": {"test": ["CMD", "true"]},
        }
    )

    assert {"tty", "ports", "healthcheck"} <= set(
        findings_for(service, expected=ServiceSpec(role="stdio"))
    )


def test_service_requires_numeric_uid_and_gid_not_an_image_username() -> None:
    service = valid_stdio()
    service["user"] = "app"

    assert "user" in findings_for(service, expected=ServiceSpec(role="stdio"))


def test_http_requires_matching_transport_health_and_loopback_bind() -> None:
    service = valid_http()
    service["environment"] = {"MCP_TRANSPORT": "stdio"}
    service["ports"] = [{"published": "8080", "target": 8080}]
    service.pop("healthcheck")

    assert {"transport", "ports", "healthcheck"} <= set(
        findings_for(
            service,
            expected=ServiceSpec(role="http", transport="http", restart="persistent"),
        )
    )


def test_materialized_credential_is_a_gate_error_without_printing_value() -> None:
    service = valid_stdio()
    service["environment"] = {"MCP_FIXTURE_API_KEY": "synthetic-secret-value"}

    findings = check_service(
        service="fixture",
        rendered=service,
        source={},
        expected=ServiceSpec(role="stdio"),
        env_prefixes=("MCP_FIXTURE_",),
        shared_env=("MCP_TRANSPORT",),
        env_file_keys=set(),
    )

    assert any(f.severity == "error" and f.rule == "secret_in_config" for f in findings)
    assert all("synthetic-secret-value" not in f.render() for f in findings)


def test_agentmail_inbox_identifier_is_sensitive_but_file_reference_is_not() -> None:
    assert _is_secret_name("AGENTMAIL_INBOX_ID")
    assert not _is_secret_name("AGENTMAIL_INBOX_ID_FILE")

    service = valid_stdio()
    service["environment"] = {"AGENTMAIL_INBOX_ID": "probe@example.invalid"}
    findings = check_service(
        service="fixture",
        rendered=service,
        source={},
        expected=ServiceSpec(role="stdio"),
        env_prefixes=("AGENTMAIL_",),
        shared_env=("MCP_TRANSPORT",),
        env_file_keys=set(),
    )
    assert any(f.severity == "error" and f.rule == "secret_in_config" for f in findings)

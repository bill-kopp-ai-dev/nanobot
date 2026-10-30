from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanobot.mcp_docker import broker
from nanobot.mcp_docker.acquisition_policy import AcquisitionPolicyError, load_acquisition_policy
from nanobot.mcp_docker.broker import BrokerError, ImageMissingError


def _policy(path: Path, *, repositories: list[str] | None = None, platforms: list[str] | None = None) -> Path:
    path.write_text(json.dumps({
        "schema_version": 1,
        "allowed_repositories": repositories if repositories is not None else ["docker.io/pbeanlabs/example-mcp"],
        "allowed_platforms": platforms if platforms is not None else ["linux/amd64"],
    }))
    path.chmod(0o444)
    return path


def test_broker_policy_is_independent_and_authorizes_only_exact_digest_and_platform(tmp_path: Path) -> None:
    policy = load_acquisition_policy(str(_policy(tmp_path / "policy.json")))
    ref = "docker.io/pbeanlabs/example-mcp@sha256:" + "a" * 64
    policy.authorize(ref, "linux/amd64")
    with pytest.raises(AcquisitionPolicyError, match="not allowed"):
        policy.authorize("docker.io/other/example-mcp@sha256:" + "a" * 64, "linux/amd64")
    with pytest.raises(AcquisitionPolicyError, match="exact OCI"):
        policy.authorize("docker.io/pbeanlabs/example-mcp:1.0.0", "linux/amd64")
    with pytest.raises(AcquisitionPolicyError, match="platform"):
        policy.authorize(ref, "linux/arm64")


def test_broker_policy_fails_closed_if_missing_writable_or_malformed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PERCIVAL_BROKER_POLICY_FILE", raising=False)
    with pytest.raises(AcquisitionPolicyError, match="not provisioned"):
        load_acquisition_policy()
    writable = tmp_path / "writable.json"
    writable.write_text("{}")
    with pytest.raises(AcquisitionPolicyError, match="non-writable"):
        load_acquisition_policy(str(writable))
    malformed = _policy(tmp_path / "malformed.json")
    malformed.chmod(0o644)
    malformed.write_text("{}")
    malformed.chmod(0o444)
    malformed.chmod(0o444)
    with pytest.raises(AcquisitionPolicyError, match="unsupported shape"):
        load_acquisition_policy(str(malformed))


def test_acquire_pulls_only_after_policy_check_and_verifies_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = "docker.io/pbeanlabs/example-mcp@sha256:" + "a" * 64
    _policy(tmp_path / "policy.json")
    monkeypatch.setenv("PERCIVAL_BROKER_POLICY_FILE", str(tmp_path / "policy.json"))
    monkeypatch.setattr(broker, "ready", lambda: None)
    calls: list[tuple[str, ...]] = []

    def inspect(source: object) -> str:
        calls.append(("inspect", str(source)))
        if len(calls) == 1:
            raise ImageMissingError()
        return str(source)

    def docker(*args: str, timeout: int = 35) -> str:
        calls.append(args)
        if args[0:2] == ("image", "inspect"):
            return "sha256:" + "b" * 64 + "|linux/amd64"
        return ""

    monkeypatch.setattr(broker, "image_reference", inspect)
    monkeypatch.setattr(broker, "docker", docker)
    result = broker.action("acquire", "example", {"reference": reference, "platform": "linux/amd64"})
    assert result == {"repositoryDigest": reference, "imageId": "sha256:" + "b" * 64, "platform": "linux/amd64"}
    assert calls[1] == ("pull", "--platform", "linux/amd64", reference)
    assert calls[-1][0:2] == ("image", "inspect")


def test_acquire_rejects_untrusted_repo_before_docker_pull(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _policy(tmp_path / "policy.json")
    monkeypatch.setenv("PERCIVAL_BROKER_POLICY_FILE", str(tmp_path / "policy.json"))
    monkeypatch.setattr(broker, "ready", lambda: None)
    monkeypatch.setattr(broker, "docker", lambda *_args, **_kwargs: pytest.fail("must not pull"))
    with pytest.raises(BrokerError, match="rejected by broker policy"):
        broker.action("acquire", "example", {
            "reference": "docker.io/other/example-mcp@sha256:" + "a" * 64,
            "platform": "linux/amd64",
        })

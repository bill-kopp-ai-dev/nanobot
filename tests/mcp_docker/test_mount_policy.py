from __future__ import annotations

from pathlib import Path

import pytest

from nanobot.mcp_docker.mount_policy import MountPolicy, host_mount_targets, resolve_host_path


def test_host_mount_table_and_symlink_aliases(tmp_path: Path) -> None:
    root = tmp_path / "host"
    for rel in ("run", "var/lib/docker", "home/bill/.nanobot", "home/bill/.nanobot/mcp-docker"):
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "var/run").symlink_to("/run")
    (root / "run/docker.sock").touch()
    (root / "home/bill/.nanobot/mcp-docker/broker-token").touch()
    info = "1 0 0:1 / / rw - ext4 /dev/sda rw\n2 1 0:2 / /home rw - ext4 /dev/sdb rw\n3 2 0:3 / /home/bill/.nanobot rw - ext4 /dev/sdc rw\n"
    assert host_mount_targets(info) == ("/", "/home", "/home/bill/.nanobot")
    assert resolve_host_path("/var/run/docker.sock", root) == "/run/docker.sock"
    policy = MountPolicy(mountinfo=info, host_root=root, docker_root="/var/lib/docker",
                         state_root="/home/bill/.nanobot",
                         token_path="/home/bill/.nanobot/mcp-docker/broker-token")
    args = policy.docker_args(None)
    assert policy.docker_args([]) == []
    assert "type=bind,src=/,dst=/host,bind-recursive=disabled" in args
    assert "type=bind,src=/home,dst=/host/home,bind-recursive=disabled" in args
    assert not any("src=/home/bill/.nanobot," in value for value in args)
    assert any("/host/var/lib/docker:" in value for value in args)
    assert any("/host/home/bill/.nanobot:" in value for value in args)
    assert not any("src=/run," in value for value in args)
    with pytest.raises(ValueError):
        policy.docker_args(["/home/bill/.nanobot"])
    with pytest.raises(ValueError):
        policy.docker_args(["/var/run"])
    with pytest.raises(ValueError):
        policy.docker_args(["/home/../run"])


def test_docker_args_empty_mounts_returns_no_args(tmp_path: Path) -> None:
    root = tmp_path / "host"
    for rel in ("run", "var/lib/docker", "home/bill/.nanobot", "home/bill/.nanobot/mcp-docker"):
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "var/run").symlink_to("/run")
    (root / "run/docker.sock").touch()
    (root / "home/bill/.nanobot/mcp-docker/broker-token").touch()
    info = "1 0 0:1 / / rw - ext4 /dev/sda rw\n2 1 0:2 / /home rw - ext4 /dev/sdb rw\n3 2 0:3 / /home/bill/.nanobot rw - ext4 /dev/sdc rw\n"
    policy = MountPolicy(mountinfo=info, host_root=root, docker_root="/var/lib/docker",
                         state_root="/home/bill/.nanobot",
                         token_path="/home/bill/.nanobot/mcp-docker/broker-token")
    assert policy.docker_args([]) == []


def test_mount_table_and_protected_paths_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        host_mount_targets("2 1 bad")
    with pytest.raises(ValueError):
        MountPolicy(mountinfo="1 0 0:1 / / rw - ext4 x rw", host_root=tmp_path,
                    docker_root="/var/lib/docker", state_root="/missing", token_path="/missing/token")

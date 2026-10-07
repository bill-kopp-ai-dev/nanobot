"""Derive the Docker MCP host mount plan from the *host* mount namespace.

The broker receives a read-only bind of /proc/1/mountinfo and of / itself for
path inspection. Missing or ambiguous inventory fails closed; never substitute
the broker container's own mount table for the daemon host's mount table.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path, PurePosixPath

_OCTAL = re.compile(r"\\([0-7]{3})")
_SKIP = ("/proc", "/sys", "/dev", "/run")


def _absolute(value: str) -> str:
    path = PurePosixPath(value)
    if not value.startswith("/") or value != str(path) or ".." in value.split("/") or "\x00" in value:
        raise ValueError("host path must be canonical and absolute")
    return value


def _inside(path: str, parent: str) -> bool:
    return path == parent or path.startswith(parent.rstrip("/") + "/")


def _unescape(value: str) -> str:
    return _OCTAL.sub(lambda match: chr(int(match.group(1), 8)), value)


def host_mount_targets(mountinfo: str) -> tuple[str, ...]:
    targets: set[str] = set()
    for line in mountinfo.splitlines():
        fields = line.partition(" - ")[0].split()
        if len(fields) < 6 or " - " not in line:
            raise ValueError("invalid host mountinfo")
        target = _unescape(fields[4])
        targets.add(_absolute(target))
    if "/" not in targets:
        raise ValueError("host mountinfo has no root mount")
    return tuple(sorted(targets, key=lambda value: (value.count("/"), value)))


def resolve_host_path(path: str, host_root: Path) -> str:
    """Resolve symlinks as host paths, never against the broker's own root."""
    pending = list(PurePosixPath(_absolute(path)).parts[1:])
    parts: list[str] = []
    hops = 0
    while pending:
        component = pending.pop(0)
        if component in ("", "."):
            continue
        if component == "..":
            if parts:
                parts.pop()
            continue
        candidate = host_root.joinpath(*parts, component)
        try:
            mode = candidate.lstat().st_mode
        except PermissionError as exc:
            raise ValueError("host path cannot be inspected") from exc
        except FileNotFoundError as exc:
            raise ValueError("host path does not exist") from exc
        if stat.S_ISLNK(mode):
            hops += 1
            if hops > 40:
                raise ValueError("host path has too many symlinks")
            target = os.readlink(candidate)
            if target.startswith("/"):
                parts = []
            pending = list(PurePosixPath(target).parts[1:] if target.startswith("/") else PurePosixPath(target).parts) + pending
        else:
            parts.append(component)
    return "/" + "/".join(parts)


class MountPolicy:
    def __init__(
        self, *, mountinfo: str, host_root: Path, docker_root: str,
        state_root: str, token_path: str, socket_path: str = "/var/run/docker.sock",
        verified_state_path: str | None = None,
    ) -> None:
        if not host_root.is_dir():
            raise ValueError("broker requires a read-only host root inventory bind")
        self.host_root = host_root
        self.targets = host_mount_targets(mountinfo)
        # Token nested under private gateway state is already masked by its
        # parent; the broker need not traverse that private directory.
        # Docker info provides the daemon's data-root, then resolve it against
        # the broker's read-only host-root view so a symlink alias cannot evade
        # the mask. If this path cannot be inspected, fail closed. Gateway state
        # is checked against docker inspect, and its token must live beneath it.
        resolved = [resolve_host_path(_absolute(docker_root), host_root),
                    _absolute(verified_state_path) if verified_state_path is not None
                    else resolve_host_path(_absolute(state_root), host_root)]
        if verified_state_path is not None and not _inside(token_path, state_root):
            raise ValueError("broker token must be inside the verified gateway state")
        resolved.append(resolved[1] if _inside(token_path, state_root) else
                        resolve_host_path(_absolute(token_path), host_root))
        socket_lexical = _absolute(socket_path)
        socket_target = resolve_host_path(socket_lexical, host_root)
        # /var/run is a conventional symlink to /run. Always cover the
        # resolved socket directory and reject both aliases as bind sources.
        if socket_lexical == "/var/run/docker.sock":
            socket_target = "/run/docker.sock"
        resolved.append(socket_target)
        if any(value == "/" for value in resolved):
            raise ValueError("protected path cannot be the host root")
        # The resolved backing paths are the mount targets. Host symlink aliases
        # resolve to these targets in /host, including /var/run -> /run.
        # A socket's parent must be covered; tmpfs cannot cover a single file.
        self.protected = tuple(sorted({
            *resolved[:3], str(PurePosixPath(resolved[3]).parent),
        }))
        for protected in self.protected:
            if protected == "/":
                raise ValueError("protected host path cannot be the root")
        # /run (and /var/run -> /run) must never be explicitly rebound.
        if not any(_inside(resolved[3], path) for path in _SKIP):
            # A custom socket elsewhere is protected by its parent, but still
            # do not blindly bind a submount containing it.
            self.protected = tuple(sorted(set(self.protected) | {str(PurePosixPath(resolved[3]).parent)}))

    def _safe(self, path: str) -> bool:
        if path in {"/var/run", "/var/run/docker.sock"}:
            return False
        try:
            canonical = resolve_host_path(path, self.host_root)
        except ValueError:
            return False
        return not any(_inside(canonical, restricted) or _inside(path, restricted) for restricted in _SKIP)

    def _covers(self, path: str, cover: str) -> bool:
        try:
            resolved_path = resolve_host_path(path, self.host_root)
        except ValueError:
            resolved_path = path
        try:
            resolved_cover = resolve_host_path(cover, self.host_root)
        except ValueError:
            resolved_cover = cover
        return _inside(cover, path) or _inside(resolved_cover, resolved_path)

    def docker_args(self, mounts: list[str] | None) -> list[str]:
        """Return bind arguments followed by covers; covers always mount last."""
        requested = ["/"] if mounts is None else [_absolute(path) for path in mounts]
        if not requested:
            raise ValueError("explicit mount reduction cannot be empty")
        if mounts is not None and "/" in requested:
            raise ValueError("full host access uses the default, not a custom mount")
        args: list[str] = []
        if mounts is None:
            submounts = [p for p in self.targets if p != "/" and self._safe(p)
                         and not any(_inside(p, cover) for cover in self.protected)]
            sources = ["/", *submounts]
        else:
            sources = requested
        for source in sources:
            if not self._safe(source) or not self.host_root.joinpath(source.lstrip("/")).exists():
                raise ValueError("mount source is unavailable or a control-plane path")
            canonical = resolve_host_path(source, self.host_root)
            if any(_inside(canonical, cover) or _inside(source, cover) for cover in self.protected):
                raise ValueError("custom mount reopens a protected host path")
            args += ["--mount", f"type=bind,src={source},dst=/host{source if source != '/' else ''},bind-recursive=disabled"]
        # Protect paths accessible through *any* selected parent, including
        # a separately bound /home; masks must be applied after every bind.
        covers = [p for p in self.protected if any(self._covers(source, p) for source in sources)]
        for path in covers:
            args += ["--tmpfs", f"/host{path}:rw,noexec,nosuid,nodev,mode=0700"]
        return args

"""F1-only offline restore rehearsal for disposable MCP Docker state.

The production service and its single writer belong to F2. This CLI refuses
non-disposable state and never reads or writes the operator's real config.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

import typer

from nanobot.utils.helpers import _write_text_atomic  # pyright: ignore[reportPrivateUsage]

app = typer.Typer(help="MCP Docker restoration (F1 disposable rehearsal only)")
_ID = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return cast(dict[str, Any], value)


def _manifest(backup_dir: Path, base: Path) -> dict[str, Any]:
    if backup_dir.is_symlink() or backup_dir.resolve().parent != base.resolve():
        raise ValueError("backup must be a direct child of the approved backup directory")
    path = backup_dir / "manifest.json"
    if path.is_symlink() or not path.is_file():
        raise ValueError("backup manifest missing or symlinked")
    manifest = _object(json.loads(path.read_text()), "manifest")
    checksum = manifest.pop("sha256", None)
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    if not isinstance(checksum, str) or not hmac.compare_digest(checksum, hashlib.sha256(canonical).hexdigest()):
        raise ValueError("backup manifest checksum mismatch")
    server_id = manifest.get("server_id")
    if manifest.get("schemaVersion") != 1 or not isinstance(server_id, str) or not _ID.fullmatch(server_id):
        raise ValueError("unsupported backup schema or server_id")
    server = _object(manifest.get("server"), "server")
    if server.get("source") is None or server.get("image") is None or not isinstance(server.get("env"), dict):
        raise ValueError("incomplete server backup")
    return manifest


def _broker(route: str, payload: dict[str, Any]) -> dict[str, Any]:
    token = os.environ["F1_BROKER_TOKEN"]
    request = urllib.request.Request(
        "http://127.0.0.1:18081/v1/" + route,
        json.dumps(payload).encode(),
        {"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return _object(json.load(response), "broker response")
    except urllib.error.HTTPError as exc:
        raise ValueError(f"broker {route} refused request (HTTP {exc.code})") from exc


@app.command("restore")
def restore(
    backup_dir: Path = typer.Argument(..., help="Direct child of config/mcp-docker/backups"),
    config: Path = typer.Option(..., "--config", help="F1 disposable config.json"),
    expected_revision: int = typer.Option(..., "--expected-revision", min=0),
    commit: bool = typer.Option(False, "--apply", help="Apply after a successful preview"),
) -> None:
    """Preview or restore one excluded server; reject races and tampered backups."""
    try:
        if os.environ.get("PERCIVAL_F1_DISPOSABLE") != "1":
            raise ValueError("restore is available only in the F1 disposable environment")
        root = Path.home() / ".nanobot"
        if config.is_symlink() or config.resolve() != (root / "config.json").resolve() or not config.is_file():
            raise ValueError("config must be the disposable gateway config.json")
        data = _object(json.loads(config.read_text()), "config")
        tools_obj = data.get("tools")
        if not isinstance(tools_obj, dict):
            raise ValueError("config.tools must be an object")
        tools: dict[str, Any] = cast(dict[str, Any], tools_obj)
        section_obj = tools.get("mcpDocker")
        if not isinstance(section_obj, dict):
            raise ValueError("config.tools.mcpDocker is required")
        section: dict[str, Any] = cast(dict[str, Any], section_obj)
        if section.get("schemaVersion") != 1:
            raise ValueError("unsupported mcpDocker schemaVersion")
        if section.get("revision") != expected_revision:
            raise ValueError(
                f"CAS conflict: persisted revision {section.get('revision')} does not match "
                f"expected {expected_revision}"
            )
        backup = _manifest(backup_dir, root / "mcp-docker" / "backups")
        server_id = cast(str, backup["server_id"])
        servers_obj = section.get("servers")
        if not isinstance(servers_obj, dict):
            raise ValueError("config.tools.mcpDocker.servers must be an object")
        servers: dict[str, Any] = cast(dict[str, Any], servers_obj)
        if server_id in servers:
            raise ValueError(f"restore refuses to overwrite existing server '{server_id}'")
        server = _object(backup["server"], "server")
        typer.echo(f"restore preview: server_id={server_id} from={backup['source_revision']} into={expected_revision + 1}")
        if not commit:
            return
        result = _broker("install", {"server_id": server_id, "image": server["source"],
                                     "persistent": server["persistent"], "env": server["env"]})
        try:
            if result.get("image") != server["image"]:
                raise ValueError(
                    f"restored image {result.get('image')} differs from backup {server['image']}"
                )
            for tool in server.get("toolsDisabled", []):
                _broker("disable-tool", {"server_id": server_id, "tool": tool})
            if not server["active"]:
                _broker("deactivate", {"server_id": server_id})
            servers[server_id] = server
            section["revision"] = expected_revision + 1
            _write_text_atomic(config, json.dumps(data, indent=2) + "\n")
            audit = root / "mcp-docker" / "audit.jsonl"
            audit.parent.mkdir(mode=0o700, exist_ok=True)
            with audit.open("a") as handle:
                handle.write(json.dumps({"action": "restore", "server_id": server_id,
                                         "revision": section["revision"], "status": "committed"}) + "\n")
            typer.echo(f"restored {server_id} at revision {section['revision']}")
        except Exception as rollback_exc:
            try:
                _broker("exclude", {"server_id": server_id, "expected_confirmation": server_id})
            except Exception as exclude_exc:
                typer.echo(f"rollback failed: could not exclude {server_id}: {exclude_exc}", err=True)
            raise rollback_exc from None
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        typer.echo(f"restore refused: {exc}", err=True)
        raise typer.Exit(1) from exc

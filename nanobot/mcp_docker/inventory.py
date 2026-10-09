"""Read-only local Docker inventory for Percival and its MCP consumers.

The Docker templates intentionally request only identity, state, labels,
ports, mounts, and health fields. Container environment values are never
requested or serialized.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

OCI_LABELS = frozenset({
    "org.opencontainers.image.title",
    "org.opencontainers.image.description",
    "org.opencontainers.image.source",
    "org.opencontainers.image.documentation",
    "org.opencontainers.image.licenses",
    "org.opencontainers.image.version",
    "org.opencontainers.image.revision",
    "org.opencontainers.image.vendor",
})
CONTAINER_LABELS = frozenset({
    "percival.mcp-docker.server-id",
    "percival.mcp-docker.owner",
    "percival.mcp-docker.managed-by",
    "percival.mcp-docker.instance-id",
})
REFERENCE_KEYS = frozenset({"reference", "image", "imageid", "image_ref", "repodigest", "repo_digest"})
SECRET_PATH_PATTERN = re.compile(
    r"(?:^|[/_.-])(?:\.env(?:$|[/_.-])|secrets?(?:$|[/_.-]))",
    re.IGNORECASE,
)
IMAGE_REFERENCE = re.compile(
    r"^(?:sha256:[0-9a-f]{64}|[A-Za-z0-9._:-]+(?:/[A-Za-z0-9._:-]+)*(?::[A-Za-z0-9._-]+|@sha256:[0-9a-f]{64}))$"
)
SEPARATOR = "\x1f"
IMAGE_TEMPLATE = SEPARATOR.join((
    "{{.Id}}", "{{json .RepoTags}}", "{{json .RepoDigests}}", "{{.Created}}",
    "{{.Os}}", "{{.Architecture}}", "{{json (index .Config \"Labels\")}}",
    "{{with index .Config \"Healthcheck\"}}{{json .Test}}{{else}}null{{end}}",
    "{{json (index .Config \"ExposedPorts\")}}",
))
CONTAINER_TEMPLATE = SEPARATOR.join((
    "{{.Id}}", "{{.Name}}", "{{.Config.Image}}", "{{.Image}}", "{{.Created}}",
    "{{.State.Status}}", "{{with index .State \"Health\"}}{{.Status}}{{else}}none{{end}}",
    "{{json (index .Config \"Labels\")}}", "{{with index .Config \"Healthcheck\"}}{{json .Test}}{{else}}null{{end}}",
    "{{json (index .HostConfig \"PortBindings\")}}", "{{json .Mounts}}",
    "{{with index .HostConfig \"Init\"}}{{json .}}{{else}}false{{end}}",
    "{{with index .HostConfig \"Tty\"}}{{json .}}{{else}}false{{end}}",
    "{{with index .Config \"Tty\"}}{{json .}}{{else}}false{{end}}",
    "{{json .Config.OpenStdin}}",
))


class DockerCommandError(RuntimeError):
    """Docker CLI query failed; stderr is omitted to avoid leaking paths/values."""


def _docker(args: list[str], *, docker_bin: str = "docker") -> str:
    try:
        result = subprocess.run([docker_bin, *args], text=True, capture_output=True, check=False)
    except OSError as exc:
        raise DockerCommandError("Docker CLI unavailable") from exc
    if result.returncode:
        operation = " ".join(args[:2])
        target = args[-1] if args and re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", args[-1]) else ""
        suffix = f" for {target}" if target else ""
        raise DockerCommandError(f"Docker {operation} query failed ({result.returncode}){suffix}")
    return result.stdout.strip()


def _json(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _labels(raw: Any, allowed: frozenset[str]) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    labels = cast(dict[str, Any], raw)
    return {str(key): str(value) for key, value in labels.items() if key in allowed and value is not None}


def _parse_image(line: str) -> dict[str, Any] | None:
    fields = line.split(SEPARATOR)
    if len(fields) != 9:
        return None
    image_id, tags, digests, created, os_name, architecture, labels, healthcheck, ports = fields
    return {
        "imageId": image_id,
        "tags": _json(tags, []),
        "repoDigests": _json(digests, []),
        "created": created,
        "os": os_name,
        "architecture": architecture,
        "labels": _labels(_json(labels, {}), OCI_LABELS),
        "healthcheck": _json(healthcheck, None),
        "exposedPorts": _json(ports, {}),
    }


def _safe_mounts(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    mounts: list[dict[str, Any]] = []
    for item in cast(list[Any], raw):
        if not isinstance(item, dict):
            continue
        mount = cast(dict[str, Any], item)
        source = str(mount.get("Source", ""))
        destination = str(mount.get("Destination", ""))
        if SECRET_PATH_PATTERN.search(source) or SECRET_PATH_PATTERN.search(destination):
            source = destination = "[REDACTED]"
        mounts.append({
            "type": mount.get("Type"),
            "source": source,
            "destination": destination,
            "readWrite": mount.get("RW") is True,
        })
    return mounts


def _parse_container(line: str) -> dict[str, Any] | None:
    fields = line.split(SEPARATOR)
    if len(fields) != 15:
        return None
    (container_id, name, configured_image, image_id, created, status, health,
     labels, healthcheck, ports, mounts, init, host_tty, tty, stdin) = fields
    labels_obj = _json(labels, {})
    return {
        "containerId": container_id,
        "name": name.lstrip("/"),
        "configuredImage": configured_image,
        "imageId": image_id,
        "created": created,
        "status": status,
        "health": health,
        "labels": _labels(labels_obj, CONTAINER_LABELS | OCI_LABELS),
        "healthcheck": _json(healthcheck, None),
        "ports": _json(ports, {}),
        "mounts": _safe_mounts(_json(mounts, [])),
        "init": _json(init, None),
        "hostTty": _json(host_tty, None),
        "tty": _json(tty, None),
        "stdinOpen": _json(stdin, None),
    }


def _relevant(value: str) -> bool:
    value = value.lower()
    return "percival" in value or "nanobot" in value or "positronic" in value


def _reference_matches_image(image: dict[str, Any], reference: str) -> bool:
    if reference == image["imageId"]:
        return True
    return reference in (image["tags"] or []) or reference in (image["repoDigests"] or [])


def _project_references(projects_root: Path) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    if not projects_root.is_dir():
        return refs
    for path in sorted(projects_root.glob("*/docker-compose.y*ml")):
        if not path.parent.name.startswith(("percival-", "nanobot")):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            match = re.match(r"^\s*image:\s*([^\s#]+)", line)
            if match:
                refs.append({"kind": "compose-image", "path": str(path), "line": str(number), "reference": match.group(1)})
    return refs


def _config_references(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    try:
        root = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    found: list[dict[str, str]] = []

    def visit(value: Any, pointer: str = "", server_id: str = "") -> None:
        if isinstance(value, dict):
            record = cast(dict[str, Any], value)
            raw_id = record.get("server_id") or record.get("serverId") or record.get("id")
            current_id = raw_id if isinstance(raw_id, str) else server_id
            for key, child in record.items():
                next_pointer = f"{pointer}/{key}"
                if (key.lower() in REFERENCE_KEYS and isinstance(child, str)
                        and IMAGE_REFERENCE.fullmatch(child)):
                    found.append({
                        "kind": "config-image-reference",
                        "path": str(path),
                        "pointer": next_pointer,
                        "serverId": str(current_id),
                        "reference": child,
                    })
                elif isinstance(child, (dict, list)):
                    visit(child, next_pointer, str(current_id))
        elif isinstance(value, list):
            for index, child in enumerate(cast(list[Any], value)):
                visit(child, f"{pointer}/{index}", server_id)

    visit(root)
    return found


def collect_inventory(*, docker_bin: str = "docker", projects_root: Path | None = None,
                      home: Path | None = None) -> dict[str, Any]:
    projects_root = projects_root or Path.home() / "Projects"
    home = home or Path.home()
    config_paths = [
        home / ".nanobot" / "config.json",
        home / ".positronic" / "mcp" / "registry.json",
        home / ".config" / "opencode" / "opencode.json",
    ]
    references = _project_references(projects_root)
    for path in config_paths:
        references.extend(_config_references(path))
    referenced_values = {item["reference"] for item in references}

    container_listing = _docker(["container", "ls", "--all", "--quiet", "--no-trunc"], docker_bin=docker_bin)
    container_ids = sorted(set(line.strip() for line in container_listing.splitlines() if line.strip()))
    containers: list[dict[str, Any]] = []
    for container_id in container_ids:
        container = _parse_container(_docker(["container", "inspect", "--format", CONTAINER_TEMPLATE, container_id], docker_bin=docker_bin))
        if container and (
            _relevant(container["name"] + " " + container["configuredImage"])
            or bool(set(container["labels"]) & CONTAINER_LABELS)
            or container["imageId"] in referenced_values
        ):
            containers.append(container)

    used_image_ids = {container["imageId"] for container in containers}
    image_listing = _docker(["image", "ls", "--all", "--quiet", "--no-trunc"], docker_bin=docker_bin)
    image_ids = sorted(set(line.strip() for line in image_listing.splitlines() if line.strip()))
    images: list[dict[str, Any]] = []
    for image_id in image_ids:
        image = _parse_image(_docker(["image", "inspect", "--format", IMAGE_TEMPLATE, image_id], docker_bin=docker_bin))
        if image and (
            _relevant(" ".join(image["tags"] or []))
            or image["imageId"] in used_image_ids
            or any(_reference_matches_image(image, value) for value in referenced_values)
        ):
            images.append(image)
    return {
        "schemaVersion": 1,
        "readOnly": True,
        "images": images,
        "containers": containers,
        "references": references,
        "redaction": "Container environment values and secret file contents are not queried or emitted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only, redacted Docker inventory for Percival MCP runtimes")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--projects-root", type=Path, default=Path.home() / "Projects")
    parser.add_argument("--docker", default=os.environ.get("DOCKER_BIN", "docker"))
    args = parser.parse_args()
    try:
        inventory = collect_inventory(docker_bin=args.docker, projects_root=args.projects_root)
    except DockerCommandError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print("# Percival Docker inventory (read-only)")
        print(f"\nImages: {len(inventory['images'])}; containers: {len(inventory['containers'])}; references: {len(inventory['references'])}.")
        print("\nEnvironment values and secret file contents are not queried or emitted.\n")
        print("## Images\n")
        print("| tags | image ID | RepoDigests | platform | created | healthcheck | selected OCI labels |")
        print("|---|---|---|---|---|---|---|")
        for image in inventory["images"]:
            labels = image["labels"]
            tags = ", ".join(image["tags"] or [])
            digests = ", ".join(image["repoDigests"] or [])
            selected_labels = json.dumps(labels, sort_keys=True, ensure_ascii=False)
            print(f"| {tags} | {image['imageId']} | {digests} | {image['os']}/{image['architecture']} | {image['created']} | {image['healthcheck']} | `{selected_labels}` |")
        print("\n## Containers\n")
        print("| name | container ID | configured image | image ID | owner | managed-by | server-id | instance-id | status/health | ports | mounts |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for container in inventory["containers"]:
            labels = container["labels"]
            mounts = ", ".join(f"{item['source']}→{item['destination']} ({'rw' if item['readWrite'] else 'ro'})" for item in container["mounts"])
            selected_labels = json.dumps(labels, sort_keys=True, ensure_ascii=False)
            print(f"| {container['name']} | {container['containerId']} | {container['configuredImage']} | {container['imageId']} | {labels.get('percival.mcp-docker.owner', '')} | {labels.get('percival.mcp-docker.managed-by', '')} | {labels.get('percival.mcp-docker.server-id', '')} | {labels.get('percival.mcp-docker.instance-id', '')} | {container['status']}/{container['health']} | {container['ports']} | {mounts} | `{selected_labels}` |")
        print("\n## Compose/config references\n")
        for reference in inventory["references"]:
            where = f"{reference['path']}:{reference.get('line', reference.get('pointer', ''))}"
            server = f" [{reference['serverId']}]" if reference.get("serverId") else ""
            print(f"- `{where}`{server}: `{reference['reference']}`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

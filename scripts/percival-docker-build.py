#!/usr/bin/env python3
"""Build the six canonical MCP images locally with source-derived identity.

The script reads ``[project].version`` from each ``pyproject.toml``,
records the full Git SHA of the checkout, refuses placeholder versions
(``0.0.0``, ``unknown``, ``local``) and runs ``docker build`` on
``linux/amd64`` only. Immutable tags follow
``percival-<service>:<version>-<shortsha>``. Pass ``--worktree-candidate``
to record the tracked-diff hash in the tag (and as a build label) when
the checkout is dirty; ``--dev-alias`` updates the mutable ``:dev``
alias in addition. Existing candidate tags are never overwritten.

The script also enforces that ``.positronic/`` and ``AGENTS.md`` are
listed in each ``.dockerignore`` before building, so the local
operator metadata is never sent to the daemon as build context.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT.parent
SERVICES = (
    "notes-mcp",
    "agentmail-mcp",
    "weather-mcp",
    "khan-calendar",
    "osm",
    "deep-research",
)
CORE_IMAGES = ("gateway", "mcp-broker")
ALL_IMAGES = SERVICES + CORE_IMAGES
SEMVER = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
INVALID_VERSIONS = {"0.0.0", "unknown", "local"}


def run(args: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"command failed ({result.returncode}): {args[0]}: {detail}")
    return result.stdout.strip()


def build(
    service: str,
    *,
    dev_alias: bool,
    worktree_candidate: bool,
    candidate_phase: str,
) -> dict[str, object]:
    is_core_image = service in CORE_IMAGES
    repo = ROOT if is_core_image else PROJECTS / f"percival-{service}"
    dockerfile = "Dockerfile.mcp-broker" if service == "mcp-broker" else "Dockerfile"
    manifest = repo / "pyproject.toml"
    if not manifest.is_file() or not (repo / dockerfile).is_file():
        raise RuntimeError(f"canonical checkout unavailable: {repo}")
    with manifest.open("rb") as stream:
        project = tomllib.load(stream).get("project", {})
    version = str(project.get("version", ""))
    if not SEMVER.fullmatch(version) or version.lower() in INVALID_VERSIONS:
        raise RuntimeError(f"invalid release version in {manifest}: {version or '(missing)'}")
    revision = run(["git", "rev-parse", "HEAD"], cwd=repo)
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError(f"checkout revision is not a full Git SHA: {repo}")
    status_lines = run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo).splitlines()
    tracked_dirty = any(not line.startswith("??") for line in status_lines)
    allowed_core_untracked = {
        "uv.lock",
        "scripts/compile_channel_locks.py",
        "docker/mcp-broker-requirements.in",
        "docker/mcp-broker-requirements.lock",
    }
    allowed_untracked: set[str] = set(allowed_core_untracked) if is_core_image else set()
    if service == "notes-mcp":
        allowed_untracked.update({
            "uv-bootstrap-requirements.in",
            "uv-bootstrap-requirements.lock",
        })
    unexpected_untracked = [
        line[3:] for line in status_lines if line.startswith("??")
        and line[3:] != "AGENTS.md" and not line[3:].startswith(".positronic/")
        and not (line[3:] in allowed_untracked or (is_core_image and line[3:].startswith("channel-locks/")))
        and not (is_core_image and line[3:].startswith(("docs/Decisions/", "docs/reports/")))
    ]
    if unexpected_untracked:
        raise RuntimeError(f"untracked source files in build context: {repo}: {unexpected_untracked}")
    if tracked_dirty and not worktree_candidate:
        raise RuntimeError(f"tracked worktree changes; commit or stash before candidate build: {repo}")
    if worktree_candidate and not tracked_dirty:
        raise RuntimeError("--worktree-candidate requires tracked changes")
    if worktree_candidate and dev_alias:
        raise RuntimeError("a worktree candidate cannot update the mutable :dev alias")

    dockerignore = (repo / ".dockerignore").read_text(encoding="utf-8").splitlines()
    ignore_patterns = {line.strip().rstrip("/") for line in dockerignore if line.strip() and not line.lstrip().startswith("#")}
    if (repo / ".positronic").exists() and not ({"**", ".positronic"} & ignore_patterns):
        raise RuntimeError(f"local .positronic metadata is not excluded from Docker context: {repo}")
    if (repo / "AGENTS.md").is_file() and not ({"**", "AGENTS.md"} & ignore_patterns):
        raise RuntimeError(f"local AGENTS.md is not excluded from Docker context: {repo}")

    dockerfile_text = (repo / dockerfile).read_text(encoding="utf-8")
    from_lines = [
        line.strip() for line in dockerfile_text.splitlines()
        if line.strip().upper().startswith("FROM ")
    ]
    base_images: list[str] = []
    for line in from_lines:
        tokens = line.split()
        base = tokens[2] if tokens[1].startswith("--") else tokens[1]
        if "@sha256:" not in base:
            raise RuntimeError(f"unpinned Docker base in {repo / dockerfile}: {base}")
        base_images.append(base)

    image = f"percival-{service}"
    diff = run(["git", "diff", "HEAD", "--binary"], cwd=repo) if worktree_candidate else ""
    if worktree_candidate:
        untracked = [
            line[3:] for line in status_lines
            if line.startswith("??") and (
                line[3:] in allowed_untracked or (is_core_image and line[3:].startswith("channel-locks/"))
            )
        ]
        diff += "".join(
            f"\n--- untracked {name} ---\n" + (repo / name).read_bytes().decode("utf-8")
            for name in sorted(untracked)
        )
    diff_sha = hashlib.sha256(diff.encode()).hexdigest() if worktree_candidate else ""
    candidate_tag = f"{version}-{revision[:7]}" + (
        f"-{candidate_phase}-{diff_sha[:12]}" if worktree_candidate else ""
    )
    tag = f"{image}:{candidate_tag}"
    existing = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", tag],
        text=True, capture_output=True, check=False,
    )
    if existing.returncode == 0:
        raise RuntimeError(f"refusing to overwrite existing image identity: {tag}")
    command = [
        "docker", "build", "--platform", "linux/amd64",
        "--build-arg", f"VERSION={version}",
        "--build-arg", f"GIT_SHA={revision}",
        "--tag", tag,
    ]
    if dev_alias:
        command += ["--tag", f"{image}:dev"]
    if worktree_candidate:
        command += [
            "--label", "io.percival.build.worktree=dirty",
            "--label", f"io.percival.build.source-diff-sha256={diff_sha}",
            "--label", f"io.percival.build.phase={candidate_phase}",
        ]
    if service == "gateway":
        command += ["--build-arg", "NANOBOT_CHANNELS=whatsapp"]
    if dockerfile != "Dockerfile":
        command += ["--file", str(repo / dockerfile)]
    command.append(str(repo))
    print(f"Building {image}:{candidate_tag} from {revision}", flush=True)
    build_process = subprocess.run(command, text=True, capture_output=True, check=False)
    if build_process.returncode:
        detail = build_process.stderr.strip() or build_process.stdout.strip()
        raise RuntimeError(f"command failed ({build_process.returncode}): docker: {detail}")
    build_log = f"{build_process.stdout}\n{build_process.stderr}"
    context_sizes = re.findall(
        r"(?m)^#\d+ \[internal\] load build context\s*\n#\d+ transferring context:\s*([0-9.]+\s*(?:B|kB|MB|GB))",
        build_log,
        re.IGNORECASE,
    )

    inspect_template = "\x1f".join((
        "{{.Id}}", "{{.Os}}", "{{.Architecture}}", "{{json .Config.Labels}}", "{{json .RepoDigests}}",
    ))
    raw = run([
        "docker", "image", "inspect", f"{image}:{candidate_tag}",
        "--format", inspect_template,
    ])
    fields = raw.split("\x1f")
    if len(fields) != 5:
        raise RuntimeError(f"unexpected Docker inspect response: {image}:{candidate_tag}")
    image_id, os_name, architecture, labels_raw, digests_raw = fields
    labels = json.loads(labels_raw or "{}")
    expected = {
        "org.opencontainers.image.title": None,
        "org.opencontainers.image.description": None,
        "org.opencontainers.image.source": (
            "https://github.com/bill-kopp-ai-dev/nanobot" if is_core_image
            else f"https://github.com/bill-kopp-ai-dev/percival-{service}"
        ),
        "org.opencontainers.image.documentation": (
            "https://github.com/bill-kopp-ai-dev/nanobot/blob/main/README.md" if service == "gateway"
            else "https://github.com/bill-kopp-ai-dev/nanobot/blob/main/docs/deployment.md" if service == "mcp-broker"
            else f"https://github.com/bill-kopp-ai-dev/percival-{service}/blob/main/README.md"
        ),
        "org.opencontainers.image.licenses": "MIT",
        "org.opencontainers.image.version": version,
        "org.opencontainers.image.revision": revision,
        "org.opencontainers.image.vendor": None,
    }
    if any((not labels.get(key) if value is None else labels.get(key) != value) for key, value in expected.items()):
        raise RuntimeError(f"built image labels do not match source: {image}:{candidate_tag}")
    if os_name != "linux" or architecture != "amd64":
        raise RuntimeError(f"built image platform mismatch: {image}:{candidate_tag}")
    lock_paths = [repo / "uv.lock"]
    if service == "notes-mcp":
        lock_paths.append(repo / "uv-bootstrap-requirements.lock")
    elif service == "gateway":
        lock_paths.extend((
            repo / "webui" / "package-lock.json",
            repo / "channel-locks" / "manifest.json",
            repo / "channel-locks" / "whatsapp.txt",
        ))
    elif service == "mcp-broker":
        lock_paths.append(repo / "docker" / "mcp-broker-requirements.lock")
    build_args = {
        name: value
        for name, value in re.findall(r"^ARG\s+(\w+)=([^\s]+)", dockerfile_text, re.MULTILINE)
        if name not in {"VERSION", "GIT_SHA"}
    }
    build_args.update({"VERSION": version, "GIT_SHA": revision})
    if service == "gateway":
        build_args["NANOBOT_CHANNELS"] = "whatsapp"
    return {
        "service": service,
        "tag": f"{image}:{candidate_tag}",
        "version": version,
        "revision": revision,
        "worktree": "dirty" if worktree_candidate else "clean",
        "sourceDiffSha256": diff_sha,
        "imageId": image_id,
        "repoDigests": json.loads(digests_raw or "[]"),
        "platform": "linux/amd64",
        "dockerfile": dockerfile,
        "baseImages": base_images,
        "lockHashes": {
            str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in lock_paths
            if path.is_file()
        },
        "buildArgs": build_args,
        "contextTransfer": context_sizes[-1] if context_sizes else "not-reported-by-builder",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("services", nargs="*", choices=ALL_IMAGES, help="default: build all six MCPs; core images are opt-in")
    parser.add_argument("--dev-alias", action="store_true", help="also point :dev at each built image")
    parser.add_argument(
        "--worktree-candidate", action="store_true",
        help="build a validation image suffixed with the worktree-diff hash; never a release identity",
    )
    parser.add_argument("--candidate-phase", choices=("f2", "f3"), default="f2")
    args = parser.parse_args()
    try:
        results = [build(
            service,
            dev_alias=args.dev_alias,
            worktree_candidate=args.worktree_candidate,
            candidate_phase=args.candidate_phase,
        )
                   for service in (args.services or SERVICES)]
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

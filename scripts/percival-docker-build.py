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
SEMVER = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
INVALID_VERSIONS = {"0.0.0", "unknown", "local"}


def run(args: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"command failed ({result.returncode}): {args[0]}: {detail}")
    return result.stdout.strip()


def build(service: str, *, dev_alias: bool, worktree_candidate: bool) -> dict[str, str]:
    repo = PROJECTS / f"percival-{service}"
    manifest = repo / "pyproject.toml"
    if not manifest.is_file() or not (repo / "Dockerfile").is_file():
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
    unexpected_untracked = [
        line[3:] for line in status_lines if line.startswith("??")
        and line[3:] != "AGENTS.md" and not line[3:].startswith(".positronic/")
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

    image = f"percival-{service}"
    diff = run(["git", "diff", "HEAD", "--binary"], cwd=repo) if worktree_candidate else ""
    diff_sha = hashlib.sha256(diff.encode()).hexdigest() if worktree_candidate else ""
    candidate_tag = f"{version}-{revision[:7]}" + (f"-f2-{diff_sha[:12]}" if worktree_candidate else "")
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
        ]
    command.append(str(repo))
    print(f"Building {image}:{candidate_tag} from {revision}", flush=True)
    run(command)

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
        "org.opencontainers.image.source": f"https://github.com/bill-kopp-ai-dev/percival-{service}",
        "org.opencontainers.image.documentation": f"https://github.com/bill-kopp-ai-dev/percival-{service}/blob/main/README.md",
        "org.opencontainers.image.licenses": "MIT",
        "org.opencontainers.image.version": version,
        "org.opencontainers.image.revision": revision,
        "org.opencontainers.image.vendor": None,
    }
    if any((not labels.get(key) if value is None else labels.get(key) != value) for key, value in expected.items()):
        raise RuntimeError(f"built image labels do not match source: {image}:{candidate_tag}")
    if os_name != "linux" or architecture != "amd64":
        raise RuntimeError(f"built image platform mismatch: {image}:{candidate_tag}")
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
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("services", nargs="*", choices=SERVICES, help="default: build all six")
    parser.add_argument("--dev-alias", action="store_true", help="also point :dev at each built image")
    parser.add_argument(
        "--worktree-candidate", action="store_true",
        help="build an F2 validation image suffixed with the tracked-diff hash; never a release identity",
    )
    args = parser.parse_args()
    try:
        results = [build(service, dev_alias=args.dev_alias, worktree_candidate=args.worktree_candidate)
                   for service in (args.services or SERVICES)]
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Audit Docker's effective context from tracked source, with synthetic secrets.

Runs no application container. BuildKit exports a scratch COPY so Docker's own
ignore semantics, not a Python approximation, decide which files are sent.
Raw evidence stays under --output's parent, outside tracked source in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path


def run(command: list[str], *, cwd: Path, input: bytes | None = None) -> bytes:
    return subprocess.run(command, cwd=cwd, input=input, capture_output=True, check=True).stdout


def audit(repo: Path, budget: int, output: Path, *, compare_head: bool = False) -> dict:
    revision = run(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    archive = run(["git", "archive", "HEAD"], cwd=repo)
    diff = run(["git", "diff", "HEAD", "--binary"], cwd=repo)
    source_dir = "nanobot" if (repo / "nanobot").is_dir() else "src"
    canaries = [
        f"{prefix}{name}" for prefix in ("", f"{source_dir}/nested/")
        for name in (".env.f3-audit", ".positronic/f3-audit", ".venv/f3-audit",
                     "secrets/f3-audit", "AGENTS.md", "__pycache__/f3-audit",
                     ".pytest_cache/f3-audit", "node_modules/f3-audit")
    ]
    canaries.extend(["reports/f3-audit", "logs/f3-audit", "tests/f3-audit"])
    results = {}
    with tempfile.TemporaryDirectory(prefix="context-audit-", dir=output.parent) as temporary:
        root = Path(temporary)
        for variant in (("head", "candidate") if compare_head else ("candidate",)):
            context = root / variant
            context.mkdir()
            with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
                stream.extractall(context, filter="data")
            if variant == "candidate" and diff:
                run(["git", "apply", "--binary", "-"], cwd=context, input=diff)
            for name in canaries:
                target = context / name
                target.parent.mkdir(parents=True, exist_ok=True)
                # Synthetic data only; never copy any real local state.
                target.write_text("F3_SYNTHETIC_CONTEXT_CANARY\n", encoding="utf-8")
            exported = root / f"{variant}-export"
            command = ["docker", "buildx", "build", "--platform", "linux/amd64",
                       "--progress", "plain", "--file", "-",
                       "--output", f"type=local,dest={exported}", str(context)]
            build = subprocess.run(command, input=b"FROM scratch\nCOPY . /context/\n",
                                   capture_output=True, check=False)
            (output.parent / f"{output.stem}-{variant}.log").write_bytes(build.stdout + build.stderr)
            if build.returncode:
                raise RuntimeError(f"BuildKit context export failed; see {output.stem}-{variant}.log")
            files = sorted(path for path in (exported / "context").rglob("*") if path.is_file())
            names = {path.relative_to(exported / "context").as_posix() for path in files}
            digest = hashlib.sha256()
            for path in files:
                digest.update(path.relative_to(exported / "context").as_posix().encode() + b"\0")
                digest.update(path.read_bytes())
            results[variant] = {
                "bytes": sum(path.stat().st_size for path in files), "fileCount": len(files),
                "contentSha256": digest.hexdigest(), "leakedCanaries": sorted(names & set(canaries)),
                "files": sorted(names),
            }
    payload = {
        "sourceSha": revision, "sourceDiffSha256": hashlib.sha256(diff).hexdigest(),
        "scope": "git archive HEAD plus tracked diff; untracked files excluded",
        "metric": "exported regular-file bytes, not incremental BuildKit transfer bytes",
        "budgetBytes": budget, "canaryCount": len(canaries), **results,
    }
    candidate = results["candidate"]
    payload["passed"] = not candidate["leakedCanaries"] and candidate["bytes"] <= budget
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--budget-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare-head", action="store_true")
    args = parser.parse_args()
    result = audit(args.repo.resolve(), args.budget_bytes, args.output.resolve(),
                   compare_head=args.compare_head)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {"head", "candidate"}}, indent=2))
    print(f"candidate: {result['candidate']['bytes']} bytes; "
          f"{len(result['candidate']['leakedCanaries'])} leaked canaries")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

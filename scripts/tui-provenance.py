#!/usr/bin/env python3
"""Generate file/hunk Git attribution for TUI and client-events at an exact commit."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVISION = "51a5d3821bce6082bd448dcd9cd8b9e213cad95b"
HEADER = re.compile(r"^([0-9a-f]{40}) \d+ (\d+)(?: \d+)?$")


@dataclass(frozen=True)
class BlameLine:
    revision: str
    line: int
    author: str
    summary: str


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def files_at(revision: str) -> list[str]:
    output = git(
        "ls-tree",
        "-r",
        "--name-only",
        revision,
        "--",
        "tui",
        "packages/client-events",
        "nanobot/cli/tui_launcher.py",
        "tests/cli/test_tui_launcher.py",
        "tests/cli/test_tui_wheels.py",
        "tests/cli/test_tui_release_packaging.py",
    )
    return [
        path
        for path in output.splitlines()
        if path
        and not path.startswith("tui/dist/")
        and not path.startswith("tui/node_modules/")
    ]


def blame_file(revision: str, path: str) -> list[BlameLine]:
    output = git("blame", "--line-porcelain", revision, "--", path)
    lines: list[BlameLine] = []
    revision_id = author = summary = ""
    final_line = 0
    for raw in output.splitlines():
        match = HEADER.match(raw)
        if match:
            revision_id, final_line = match.group(1), int(match.group(2))
        elif raw.startswith("author "):
            author = raw.removeprefix("author ")
        elif raw.startswith("summary "):
            summary = raw.removeprefix("summary ")
        elif raw.startswith("\t"):
            lines.append(BlameLine(revision_id, final_line, author, summary))
    return lines


def hunks(lines: list[BlameLine]) -> list[tuple[int, int, BlameLine]]:
    if not lines:
        return []
    result: list[tuple[int, int, BlameLine]] = []
    start = previous = lines[0].line
    current = lines[0]
    for item in lines[1:]:
        same_origin = (
            item.revision == current.revision
            and item.author == current.author
            and item.summary == current.summary
        )
        if same_origin and item.line == previous + 1:
            previous = item.line
            continue
        result.append((start, previous, current))
        current = item
        start = previous = item.line
    result.append((start, previous, current))
    return result


def generate(revision: str) -> str:
    resolved = git("rev-parse", revision).strip()
    paths = files_at(resolved)
    if not paths:
        raise RuntimeError(f"no tui/src or packages/client-events files at {resolved}")
    rows: list[tuple[str, int, int, BlameLine]] = []
    for path in paths:
        rows.extend((path, start, end, origin) for start, end, origin in hunks(blame_file(resolved, path)))
    lines = [
        "# Percival TUI and packaging source lineage",
        "",
        f"**Candidate revision:** `{resolved}`",
        f"**Files covered:** {len(paths)}",
        f"**Attributed contiguous hunks:** {len(rows)}",
        "**Method:** Git `blame --line-porcelain`, preserving upstream commit attribution and local edits. Coverage includes TUI source, package/relinking/release files, shared client-events, launcher and packaging tests; generated `tui/dist/` artifacts are excluded. This is a technical provenance map, not a legal opinion or B13 approval.",
        "",
        "| File | Lines | Commit | Author recorded by Git | Commit subject recorded by Git |",
        "|---|---:|---|---|---|",
    ]
    for path, start, end, origin in rows:
        subject = origin.summary.replace("|", "\\|")
        author = origin.author.replace("|", "\\|")
        lines.append(f"| `{path}` | {start}-{end} | `{origin.revision[:12]}` | {author} | {subject} |")
    lines.extend([
        "",
        "The code itself and the Git attribution were not rewritten. Commit authorship is historical metadata, not proof of copyright ownership or license compliance. Release notices, corresponding-source offer, Bun/OpenTUI materials, exact clean-SHA build and owner review remain separate gates.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/provenance/tui-lineage-51a5d382.md")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = generate(args.revision)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != content:
            raise SystemExit(f"stale or missing provenance map: {output}")
        print(f"provenance map current: {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

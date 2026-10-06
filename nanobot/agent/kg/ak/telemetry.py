"""Append-only JSONL telemetry for AK multimodal operations.

Mirrors ``percival-acquire-knowledge/telemetry.py``.  Telemetry lives
under ``<bundle>/.telemetry/events.jsonl`` (D33: gitignored) so it can
be excluded from backups alongside the other AK gitignored
directories.  The helper never raises — telemetry must not be able to
take down the tool that emitted it.
"""

from __future__ import annotations

import json
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVENTS_FILE = ".telemetry/events.jsonl"
_NS_PER_S = 1_000_000_000


def _events_path(root: Path) -> Path:
    return root / EVENTS_FILE


def track(root: Path, operation: str, **fields: Any) -> None:
    """Append a single event to the JSONL log (best-effort)."""
    try:
        events_path = _events_path(root)
        events_path.parent.mkdir(parents=True, exist_ok=True)
        event = {"ts": datetime.now(timezone.utc).isoformat(), "op": operation, **fields}
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, default=str))
            handle.write("\n")
    except OSError:
        pass


@contextmanager
def track_op(root: Path, operation: str, **fields: Any) -> Generator[dict[str, Any], None, None]:
    """Time the wrapped block and emit a single event on exit (success or raise)."""
    extra: dict[str, Any] = dict(fields)
    started = time.monotonic_ns()
    try:
        yield extra
    finally:
        extra["duration_s"] = (time.monotonic_ns() - started) / _NS_PER_S
        track(root, operation, **extra)


def stats(root: Path) -> dict[str, Any]:
    """Aggregate counters from the JSONL log (best-effort)."""
    events_path = _events_path(root)
    if not events_path.exists():
        return {
            "events_total": 0,
            "by_operation": {},
            "diskcache_hit_rate": {"image_caption": None, "audio_transcribe": None},
            "cost_usd_total": 0.0,
            "last_event_ts": None,
        }
    by_op: dict[str, int] = {}
    image_hits = image_misses = audio_hits = audio_misses = 0
    cost_total = 0.0
    last_ts: str | None = None
    try:
        with events_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                op = event.get("op", "unknown")
                by_op[op] = by_op.get(op, 0) + 1
                if op == "image_caption" and "cache_hit" in event:
                    if event["cache_hit"]:
                        image_hits += 1
                    else:
                        image_misses += 1
                elif op == "audio_transcribe" and "cache_hit" in event:
                    if event["cache_hit"]:
                        audio_hits += 1
                    else:
                        audio_misses += 1
                cost = event.get("cost_usd")
                if isinstance(cost, (int, float)):
                    cost_total += cost
                ts = event.get("ts")
                if ts:
                    last_ts = ts
    except OSError:
        pass

    def hit_rate(hits: int, misses: int) -> float | None:
        total = hits + misses
        if total == 0:
            return None
        return hits / total

    return {
        "events_total": sum(by_op.values()),
        "by_operation": by_op,
        "diskcache_hit_rate": {
            "image_caption": hit_rate(image_hits, image_misses),
            "audio_transcribe": hit_rate(audio_hits, audio_misses),
        },
        "cost_usd_total": cost_total,
        "last_event_ts": last_ts,
    }


__all__ = ["stats", "track", "track_op"]

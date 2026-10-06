"""CM enrich policy: validate, propose, then write only allowlisted metadata with CAS."""

from __future__ import annotations

import asyncio
from pathlib import Path
from time import monotonic
from typing import Any

from loguru import logger

from nanobot.agent.kg.cm import core, enricher
from nanobot.agent.kg.vendor.okf_bundle_core.schema import validate_id
from nanobot.config.kg import PercivalKgConfig
from nanobot.utils.llm_runtime import LLMRuntime

FIELDS = frozenset({"summary", "tags", "supersedes"})


async def memory_enrich(
    root: Path, note_id: str, *, config: PercivalKgConfig, runtime: LLMRuntime | None,
    fields: list[str] | None = None, force_regen: bool = False,
    reason: str = "nightly enrich",
) -> dict[str, Any]:
    validate_id(note_id)
    selected = set(fields or FIELDS)
    if selected - FIELDS:
        raise ValueError(f"Invalid enrich fields: {sorted(selected - FIELDS)}")
    if runtime is None:
        return {"status": "error", "id": note_id, "reason": reason,
                "error_kind": "runtime_unavailable", "error": "No LLM runtime selected for this request"}
    start = monotonic()
    # Both read and write boundaries are checked before any external request.
    note = await asyncio.to_thread(core.notes_read, root, note_id)
    await asyncio.to_thread(core.check_bundle_paths, root, write=True)
    fm = note["frontmatter"]
    if not force_regen and "summary" in selected and fm.get("summary"):
        return {"status": "skipped", "id": note_id, "reason": "already enriched (set force_regen=True to overwrite)"}

    remaining = config.cm_enrich_timeout_s - (monotonic() - start)
    if remaining <= 0:
        return {"status": "error", "id": note_id, "reason": reason, "error_kind": "timeout", "error": "CM enrich deadline exceeded"}
    try:
        tags = await asyncio.to_thread(enricher.known_tags, root)
        remaining = config.cm_enrich_timeout_s - (monotonic() - start)
        if remaining <= 0:
            raise enricher.EnrichmentUnavailableError("timeout")
        proposal = await asyncio.wait_for(enricher.propose(note, tags, runtime=runtime), timeout=remaining)
    except (enricher.EnrichmentUnavailableError, TimeoutError) as exc:
        kind = exc.kind if isinstance(exc, enricher.EnrichmentUnavailableError) else "timeout"
        return {"status": "error", "id": note_id, "reason": reason, "error_kind": kind,
                "error": f"CM enrichment failed: {kind}"}
    except ConnectionError:
        return {"status": "error", "id": note_id, "reason": reason, "error_kind": "connection",
                "error": "CM enrichment failed: connection"}

    patch: dict[str, Any] = {}
    if "summary" in selected and proposal.summary != fm.get("summary"):
        patch["summary"] = proposal.summary
    if "tags" in selected:
        tags_now = list(fm.get("tags") or [])
        for tag in proposal.tags_add:
            tag = tag.strip().lower()
            if tag and tag not in tags_now:
                tags_now.append(tag)
        for tag in proposal.tags_remove:
            if tag in tags_now:
                tags_now.remove(tag)
        if tags_now != (fm.get("tags") or []):
            patch["tags"] = tags_now
    if "supersedes" in selected:
        replaced = list(fm.get("supersedes") or [])
        for target in proposal.supersedes:
            if target not in replaced:
                replaced.append(target)
        if replaced != (fm.get("supersedes") or []):
            patch["supersedes"] = replaced
    if not patch:
        return {"status": "written", "id": note_id, "reason": "no-op (no fields to update)",
                "content_hash": note["content_hash"], "body_hash": note["body_hash"],
                "frontmatter": fm, "confidence": proposal.confidence}
    if monotonic() - start >= config.cm_enrich_timeout_s:
        return {"status": "error", "id": note_id, "reason": reason, "error_kind": "timeout", "error": "CM enrich deadline exceeded"}
    result = await asyncio.to_thread(
        core.notes_write, root, note_id=note_id, body=note["body"],
        frontmatter_patch=patch, expected_body_hash=note["body_hash"],
        reason=f"enrich: {reason} (confidence={proposal.confidence})",
    )
    elapsed = monotonic() - start
    late = {}
    if elapsed > config.cm_enrich_timeout_s:
        logger.warning("CM enrich write completed after timeout budget: {:.2f}s", elapsed)
        late = {"elapsed_s": round(elapsed, 3), "deadline_exceeded_after_write": True}
    return {"status": "written", "id": note_id, "reason": reason, **result,
            "confidence": proposal.confidence, **late}

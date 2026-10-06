---
name: ak-onboard-source
description: Onboard a Source into AK with deduplication, inspection, atomization and links.
---

# Onboard an acquired Source

Adapted from `prompt_workflow_onboard_source` (first-time and batch). For a single source, search likely title/author with `ak_source_search` to spot duplicates, then ingest with `ak_source_ingest(src_path=...)` only when authorized to read the input. The native tool enforces the agent's workspace access policy; it does not promise access to arbitrary absolute paths. Record `source_id`, `chunks_total`, `sha256` and `reused_existing`. Inspect metadata with `ak_source_list(kind="Source")`, and preview individual chunks with `ak_source_read(source_id, chunk_index=0)`.

Use `ak-atomize` to create ExtractedNotes for useful missing chunks, then `ak-link` for defensible lateral links across Sources. Verify `ak_source_stats`; a reused binary may still have missing chunks. For a batch, automatic SHA-256 deduplication is not semantic deduplication: track source IDs per input and sample title/author collisions before accepting duplicates. Do not promise all chunks are processed when choosing a subset.

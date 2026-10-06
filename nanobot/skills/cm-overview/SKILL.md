---
name: cm-overview
description: Orientation to native collective-memory notes, links, enrichment and policy tools.
---

# Collective memory: orientation

Adapted from the legacy CM `prompt_cm_overview`. The bundle is `.collective-memory/` under the effective workspace or configured parent root. Use `cm-notes-write`, `cm-link`, `cm-capture-session`, `cm-audit-health`, and `cm-rebuild-graph` for focused guidance.

- Before creating a note, search with `cm_notes_search`, read candidates with `cm_notes_read`, then write with `cm_notes_write` and the appropriate hash CAS. `cm_note_history` reads commits. Search is literal and case-insensitive; it does not require ripgrep.
- Link notes with `memory_link` or `memory_batch_link` (either `edges` or aligned `from_ids`/`to_ids`/`relations`). Batch results are per-edge, not atomic. Forward references are permitted.
- `cm_memory_enrich` proposes summary, tags and supersedes using the model and provider selected for this turn. It only writes frontmatter with body-hash CAS. Without an active runtime it reports `runtime_unavailable` and does not write. Check `status` (`written`, `skipped`, `error`). Avoid unnecessary retries and repeated enrichment.
- `memory_stats` reports health and policy; `graph_neighbors`/`graph_shortest_path` query an existing graph, not rebuild it. `memory_aging_candidates` only suggests candidates; `memory_set_lifecycle` and `memory_flag_for_review` change policy. `memory_set_protected` and `memory_resolve_review` require a human decision. Do not archive (`memory_forget`) solely to reduce orphan counts.
- `asset_get_path` resolves an existing asset; `memory_attach` associates it with a note. `memory_storage_stats` and dry-run `memory_repo_maintenance` report storage; actual GC requires write access.

Legacy MCP prompt tools are replaced by these discoverable skills. In `kg.mode=mcp`, use the legacy server's names; in `native`/`both`, use the native tool names above.

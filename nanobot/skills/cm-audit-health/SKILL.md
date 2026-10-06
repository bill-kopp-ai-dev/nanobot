---
name: cm-audit-health
description: Interpret CM memory_stats health, review, graph and storage signals without automatic destructive action.
---

# Audit collective-memory health

Adapted from `prompt_audit_health`. Call `memory_stats(include_storage=False)` for notes, orphans, tags/types distributions, inbox, recent writes, protection, cold notes, pending review and graph health. `recent_writes` is ordered by mtime and limited to 50; filter timestamps on the caller side for a session window. `orphans` excludes cold and permanently excluded development notes: disconnected total is `len(orphans) + cold_count + excluded_permanent` when those fields are available. Orphans can be legitimate.

`pending_review_ids` and `flagged_by_kind` are a human review queue; do not resolve flags automatically. `memory_flag_for_review` needs a real note ID, not a sentinel for bundle-wide health. `protected_count` reflects human protection; do not toggle it to simplify automation.

`graph_health.last_build` is the graph artifact modification time. Missing or stale graph artifacts merit a separate rebuild decision. For storage use either `memory_stats(include_storage=True)` or `memory_storage_stats()`, not both in the same turn. `memory_repo_maintenance()` is dry-run by default; inspect it before requesting actual GC.

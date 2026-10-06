---
name: ak-rebuild-graph
description: Rebuild the native AK graph JSON deterministically after source or link changes.
---

# Rebuild the acquired-knowledge graph

Adapted from `prompt_runbook_rebuild_graph`, updated for F8. Inspect `ak_source_stats` or `ak_graph_neighbors` first when only reading; note writes do not rebuild derived data. Check root and layout using `nanobot kg doctor --json` and run `nanobot kg graph rebuild ak --json` to atomically replace `graphify-out/graph.json` under a lock. For another workspace pass `--workspace <path>` before `graph`; `--bundle-root <parent-or-bundle>` is an option on `rebuild`. Inspect `nodes`, `edges`, `edges_collapsed`, `edges_dangling` and `dangling_edges`; investigate missing targets rather than creating speculative links.

This deterministic builder does not invoke graphify `cluster-only` or `update`, does not label communities via an LLM and does not produce `graph.html` or `GRAPH_REBUILD_REPORT.md`. The SPA reads authenticated node-link JSON. Keep the legacy `ak-graph-rebuild` only for explicit rollback after compatibility testing.

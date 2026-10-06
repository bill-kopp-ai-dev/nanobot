---
name: cm-rebuild-graph
description: Distinguish CM graph inspection from a rebuild and interpret derived graph artifacts.
---

# Rebuild the collective-memory graph

Adapted from `prompt_runbook_rebuild_graph`. `graph_neighbors`, `graph_shortest_path`, and `memory_stats().graph_health` inspect existing derived artifacts; note writes do not rebuild the graph. Do not run a rebuild merely to answer a graph query. A missing graph must be rebuilt before graph queries work.

Run `nanobot kg doctor --json` first to confirm the selected bundle; for a different workspace pass `--workspace <path>` before `graph`. Run `nanobot kg graph rebuild cm --json` only with authorization to write to that bundle. `--bundle-root <parent-or-bundle>` selects an explicit root; inspect `nanobot kg graph rebuild --help` for options. The command uses the vendored deterministic graph builder under a lock and atomically replaces `graphify-out/graph.json`. Its report has `nodes`, `edges`, `edges_collapsed`, `edges_dangling`, and `dangling_edges`; review missing targets instead of forcing links. It does not run graphify clustering, label communities, emit `graph.html` or `GRAPH_REBUILD_REPORT.md`. The native SPA reads authenticated graph data from this JSON. Keep legacy rebuild commands for explicit rollback only.

---
name: cm-rebuild-graph
description: Distinguish CM graph inspection from a rebuild and interpret derived graph artifacts.
---

# Rebuild the collective-memory graph

Adapted from `prompt_runbook_rebuild_graph`. `graph_neighbors`, `graph_shortest_path`, and `memory_stats().graph_health` inspect existing derived artifacts; note writes do not rebuild the graph. Do not run a rebuild merely to answer a graph query. A missing graph must be rebuilt before graph queries work.

The native `nanobot kg graph rebuild cm` command is planned for F8 and is not yet available. Until then, use an explicitly installed legacy `cm-graph-rebuild` only when working on an authorized copy of the bundle and the toolchain is configured. Inspect its dry-run and report before using its outputs; do not assume `graph_nodes`/`graph_edges` (pre-cluster) equal the served `graph_nodes_served`/`graph_edges_served` (post-cluster). Check `cluster_only_ok`, dropped dangling edges and the resulting `graph.json` under `graphify-out/`. Avoid `graphify update`, which builds a different graph from markdown.

---
name: ak-audit-health
description: Interpret AK source_stats, graph and binary integrity signals before maintenance.
---

# Audit acquired-knowledge health

Adapted from `prompt_audit_health`. Use `ak_source_stats` for `sources_total`, `extracted_total`, `partially_atomized`, `orphan_extracted`, `laterally_isolated` and `broken_file_path`. Partial atomization can be intentional for sampled Sources; compare `chunks_total` to `chunks_atomized` before resuming. Orphan extracted notes have invalid `derived_from` targets; isolated notes lack lateral links but can have a valid Source. Never force edges just to make a metric zero. `broken_file_path` calls for investigation of `sources/` and the bundle's Git log, not deletion.

Use `ak_get_laterally_isolated_notes` to list candidates for human-curated lateral linking. `nanobot kg doctor --json` checks both bundles and graph artifact; `nanobot kg graph rebuild ak --json` regenerates the derived JSON only when a rebuild is needed. Cache and telemetry, where present, are separate from the canonical notes and raw binary backup.

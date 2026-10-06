---
name: ak-atomize
description: Resume atomization of an acquired Source into ExtractedNotes without duplicate chunks.
---

# Atomize an acquired Source

Adapted from `prompt_runbook_atomize`. Inspect `ak_source_list(kind="Source")` for `chunks_total` and `chunks_atomized`; `ak_source_read(source_id, chunk_index)` reads **one** chunk of a Source, not aggregated metadata. Prioritize missing chunk indexes and check their content before writing. For each useful chunk call `ak_note_write_extracted(source_id, chunk_index, title, body)`; check its per-call `applied` status. Do not overwrite an existing extracted note by repeating the call.

Seek up to three justified lateral links to notes from other Sources with `ak_source_search` and `ak_note_link`; substring search is not semantic discovery, so confirm the candidate's meaning first. `derived_from` to the original Source is created by extraction; do not duplicate it. No plausible neighbor is an acceptable outcome. Recheck `ak_source_stats().partially_atomized` and the Source's missing indexes; not every chunk must be atomized if the scope intentionally samples a large source.

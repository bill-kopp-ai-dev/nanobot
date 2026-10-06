---
name: ak-link
description: Choose AK link relations using the D65 precedence and avoid cross-bundle edges.
---

# Link acquired-knowledge notes

Adapted from `prompt_runbook_link`. Confirm the source is a Source or ExtractedNote in AK and understand both endpoints; `ak_source_list` gives metadata, `ak_source_read` reads a Source chunk only, while `ak_source_search` searches note text. Use the first applicable relation: `supersedes` (replacement) > `contradicts` (evidence in tension) > `derived_from` (extraction or synthesis) > `related` (genuine association). `derived_from` and `supersedes` are frontmatter; lateral `related` and `contradicts` live in `## Links` in the body for graph visibility.

Call `ak_note_link(from_id, to_id, relation)` and inspect `applied`; forward targets are allowed but must belong to the same AK bundle, never CM. `ak_note_batch_link` processes edges separately, not atomically: inspect each result and reconcile partial success. Do not link just to reduce `laterally_isolated`. Rebuild the graph separately with `nanobot kg graph rebuild ak` when derived data must reflect writes.

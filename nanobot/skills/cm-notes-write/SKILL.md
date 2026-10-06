---
name: cm-notes-write
description: Write or update a CM note safely using search, read and hash compare-and-swap.
---

# Write a collective-memory note

Adapted from `prompt_runbook_write_note`.

1. Search for duplicates using `cm_notes_search(query)`; read plausible hits with `cm_notes_read(id)`.
2. For an existing note, read it immediately before writing. Keep the returned `body_hash` and `content_hash`. For frontmatter-only edits use `expected_body_hash`; for an entire content edit use `expected_content_hash`. On a CAS mismatch, re-read and reconcile instead of blindly retrying.
3. Call `cm_notes_write(id, body, frontmatter_patch, expected_*_hash, reason)`. On creation the note has no prior hash. Never assume arbitrary frontmatter keys are patchable: verify the returned frontmatter.
4. If there is a real relation, call `memory_link(from_id, to_id, relation)`; choose the relation using `cm-link`. A standalone note need not have a fabricated edge.

`cm_memory_enrich` uses the provider, model and generation settings selected for this turn for proposals limited to summary, tags and supersedes. Without a turn runtime it returns `runtime_unavailable` without writing; it does not grant authority to change sources, verification or policy fields.

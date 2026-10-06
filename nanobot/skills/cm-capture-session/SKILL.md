---
name: cm-capture-session
description: Review CM notes, meaningful links, inbox assets and drafts when closing a session.
---

# Capture a session in collective memory

Adapted from `prompt_workflow_capture_session`.

1. Review notes created or updated in this session; identify missing context and use `memory_link` only for genuine relations.
2. Call `memory_stats()` once to inspect `orphans` and `untriaged_inbox`. Standalone notes can be legitimate; do not force edges to make the count smaller.
3. Attach relevant inbox assets with `memory_attach` after verifying their paths. Keep drafts in `notes/` with a tag until there is an explicit decision to archive.
4. Present candidates for human review rather than invoking `memory_forget` on the basis of age or a draft tag alone. An archived note moves to `_archive/`.

Use `cm-audit-health` for interpreting stats and `cm-notes-write` for CAS-safe edits.

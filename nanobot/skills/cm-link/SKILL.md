---
name: cm-link
description: Choose a semantic relation between CM notes and avoid misleading graph links.
---

# Link collective-memory notes

Adapted from `prompt_runbook_link` (D65). Read both notes when they exist and use the first relation that actually applies:

- `supersedes`: A replaces an obsolete B; stored in frontmatter. B is not automatically archived.
- `contradicts`: A and B disagree while both retain value; represented in the body.
- `derived_from`: A is an extraction or specialization of B; stored in frontmatter.
- `related`: context/navigation, represented in the body. Do not use it merely to lower an orphan count.

`memory_link(from_id, to_id, relation)` permits a forward target reference. For multiple edges, `memory_batch_link` accepts `edges` or aligned `from_ids`/`to_ids`/`relations` arrays; failures can leave earlier edges applied, so inspect per-edge status. Archiving a superseded note is a separate human decision using `memory_forget`.

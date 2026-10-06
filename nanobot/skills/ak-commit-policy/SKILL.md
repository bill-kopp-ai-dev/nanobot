---
name: ak-commit-policy
description: Preserve AK bundle layout, Git and filesystem guards during changes or migration.
---

# Acquired-knowledge bundle guardrails

Adapted from `prompt_guardrails_commit_policy`. Keep `sources/` binary payloads out of Git; `GitStore.commit_paths` rejects inbox commits, so a Git backup **does not** back up these files. Preserve `notes/`, `sources/`, `graphify-out/`, `.git/`, `log.md` and archive in a complete backup. Do not create a legacy `_inbox/`. Mutations use the bundle lock and atomic file replacement; never edit graph or note files concurrently with another writer. Paths and symlinks must stay within the authorized workspace and bundle.

The four relations are `supersedes`, `contradicts`, `derived_from`, `related`; D65 precedence is described in `ak-link`. The native tools use the request's provider for image caption, while unsupported audio returns `unsupported_capability`, not a fabricated transcript. For one-shot legacy lateral-link repair, inspect `nanobot kg ak-migrate-lateral-links --json` before `--apply` on a verified copy: cross-bundle and broken targets are reported and left alone. Do not equate migration of links with deletion of source binaries.

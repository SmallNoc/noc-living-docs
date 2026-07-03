# Agent Protocol

This protocol defines how AI coding agents should use NOC Living Docs.

## Fixed Root

Use `noc_docs/` as the only living documentation root.

Forbidden:

- Do not create `docs/` for this protocol.
- Do not split this protocol between `docs/` and `noc_docs/`.
- Do not migrate existing `docs/` content unless the user explicitly requests it.

## Before Code Changes

1. Read the project agent entry file, such as `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`.
2. Read `noc_docs/docs-map.md`.
3. Identify the affected feature or domain.
4. Read only the relevant feature or domain docs.
5. Treat `guardrails.md` as hard constraints.

## After Code Changes

1. Update `status.md` when current behavior changes.
2. Update `requirements.md` when intended behavior changes.
3. Append `change-record.md` for important behavior, compatibility, migration, or architecture changes.
4. Append `test-record.md` with verification results.
5. Update indexes when features or domains are added, renamed, or removed.
6. Report which docs were checked, updated, or intentionally left unchanged.

## Conflict Handling

If documentation conflicts with code:

- Prefer code for current behavior and update `status.md`.
- Do not infer product intent from code alone.
- Record unresolved intent conflicts in `notes.md`.
- Stop and ask the user if the request conflicts with `guardrails.md`.


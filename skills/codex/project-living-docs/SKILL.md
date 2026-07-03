---
name: project-living-docs
description: Use when initializing, auditing, querying, or maintaining project living documentation for AI-assisted development, especially when code changes may affect requirements, current behavior, guardrails, tests, change history, Git workflow, or agent guidance.
---

# Project Living Docs

Use NOC Living Docs as executable project memory: route through indexes, read the smallest relevant docs, update current behavior and verification records when code changes.

## Non-Negotiables

- Use `noc_docs/` as the fixed documentation root.
- Do not create `docs/` for this protocol.
- Do not overwrite existing `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`.
- Preserve existing user rules and merge NOC rules in a managed block.
- Use Chinese prose by default and English structure for file names, headings, IDs, JSON keys, and status values.
- Treat code as current behavior; treat `requirements.md` as product intent.
- Read only relevant docs for normal development unless auditing.

## Execution Loop

1. Identify the task type: initialize, code change, docs query, audit, or migration.
2. Identify affected feature/domain from user request, changed paths, and `noc_docs/.living-docs/feature-map.json`.
3. Read common routing files: agent entry file, `noc_docs/docs-map.md`, and `.living-docs/*.json` when present.
4. Choose Light, Deep, Audit, or Query mode.
5. Read required docs using the fallback rules below.
6. Make the requested change.
7. Update NOC docs when behavior, intent, guardrails, tests, or feature lists changed.
8. Run `python scripts/noc.py index <project>` after doc structure or feature mapping changes.
9. Run `python scripts/noc.py check <project> --staged --warn-only` before commits when Git is available.
10. Final response must list NOC docs checked, updated, or intentionally unchanged.

## Modes

| Mode | Use When | Read Scope |
|---|---|---|
| Light | narrow implementation or bug fix | entry file, `docs-map.md`, feature map, affected `agent-guide.md`, `guardrails.md` |
| Deep | new feature, refactor, API/data/security behavior change | Light docs plus `requirements.md`, `status.md`, `test-record.md`, `change-record.md` |
| Audit | initialization, migration, consistency review | full `noc_docs/` tree as needed |
| Query | answering docs questions | route through index, then read smallest relevant docs |

Escalate Light to Deep when changed code affects behavior, requirements, tests, security, public API, data schema, persistence, permissions, billing, deployment, or cross-feature contracts.

## Read Fallbacks

For each affected feature:

1. Read feature `agent-guide.md` if present.
2. Read feature `guardrails.md` if present.
3. If feature guardrails are missing in Domain Mode, read `noc_docs/domains/<domain>/guardrails.md`.
4. If feature docs are missing or no feature maps to the changed path, read `noc_docs/docs-map.md`, `noc_docs/project-status.md`, and the closest domain or feature index.
5. If `feature-map.json` has `completeness.complete=false`, missing docs, or stale-looking entries, say so and use Deep mode.

Do not invent requirements to fill missing docs. Record the gap in `status.md`, `notes.md`, or the final response.

## Initialize

Prefer the repository script when available:

```bash
python scripts/noc.py init /path/to/project
python scripts/noc.py validate --target /path/to/project
```

If the scripts are unavailable:

1. Scan the project structure, package files, apps/services, existing docs, and agent entry files.
2. Decide Small Mode or Domain Mode.
3. Create `noc_docs/` from templates if missing.
4. Create or merge the project agent entry file.
5. Create `.living-docs/config.json` with `language: zh-CN` and `machine_keys: en-US`.
6. Report the mode decision and the files created or merged.

Default to Small Mode unless evidence supports Domain Mode. Use Domain Mode when any condition applies:

- feature count is 20 or more
- domain count is 3 or more
- app/service count is 3 or more
- monorepo is detected
- domain-level guardrails are required

When choosing Domain Mode, explain the specific trigger. Example: `Domain Mode because this repo has 4 services and shared domain-level guardrails.`

Never initialize both `features/` and `domains/` unless the user explicitly requests migration planning.

## Maintain During Development

Before editing code:

1. Identify affected feature or domain from changed paths, task text, and `.living-docs/feature-map.json` if available.
2. Read affected `agent-guide.md` and `guardrails.md`.
3. Read `requirements.md`, `status.md`, and `test-record.md` when behavior, requirements, or verification may change.

After editing code:

1. Update `status.md` when actual behavior changes.
2. Update `requirements.md` only when intended behavior changes.
3. Append `change-record.md` for important changes.
4. Append `test-record.md` with verification results.
5. Update indexes when feature or domain lists change.
6. Final response must say which NOC docs were checked, updated, or intentionally unchanged.

After documentation changes, run the index script when available:

```bash
python scripts/noc.py index /path/to/project
```

Before commits, use the change check when available:

```bash
python scripts/noc.py check /path/to/project --staged --warn-only
```

The installed Git hook is advisory by default. It should warn when code changes lack related staged `noc_docs/` changes, but it must not block commits that intentionally leave docs unchanged.

When changed paths do not map to a feature, use mapping suggestions if available:

```bash
python scripts/noc.py suggest-map /path/to/project
```

Treat suggestions as candidates. If the mapping is clear from the project structure or user intent, merge them with:

```bash
python scripts/noc.py suggest-map /path/to/project --write
```

Do not use `--write` when the suggested feature names are ambiguous.

## Index Trust Signals

Use `.living-docs/feature-map.json` for routing, but treat it as a cache.

- `paths` maps code paths to features.
- `freshness.last_doc_update` shows the newest source doc update for a feature.
- `completeness.missing_docs` lists missing expected feature docs.
- `completeness.complete=false` means answer cautiously and prefer Deep or Audit mode.

## Conflict Handling

If docs conflict with code, treat code as current behavior and update `status.md`.

If requirements conflict with code, do not silently rewrite requirements. Ask the user when product intent is unclear.

If the user request conflicts with `guardrails.md`, stop before editing and ask for explicit confirmation.

## Managed Block

When adding NOC rules to an existing agent file, use:

```md
<!-- noc-living-docs:start -->
...
<!-- noc-living-docs:end -->
```

Only replace text inside this block on future updates.

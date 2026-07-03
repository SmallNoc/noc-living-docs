---
name: project-living-docs
description: Use when initializing, auditing, querying, or maintaining project living documentation for AI-assisted development, especially when code changes may affect requirements, current behavior, guardrails, tests, change history, Git workflow, or agent guidance.
---

# Project Living Docs

Use the NOC Living Docs protocol to keep project documentation useful as agent working context and development constraints.

## Hard Rules

- Use `noc_docs/` as the fixed documentation root.
- Do not create `docs/` for this protocol.
- Do not overwrite existing `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`.
- Preserve existing user rules and merge NOC rules in a managed block.
- Use Chinese prose by default and English structure for file names, headings, IDs, JSON keys, and status values.
- Read only relevant docs for normal development.

## Modes

| Mode | Use When | Read Scope |
|---|---|---|
| Light | normal development | agent entry file, `docs-map.md`, feature map, affected `agent-guide.md`, `guardrails.md` |
| Deep | new features, refactors, API changes, security-sensitive changes | Light docs plus requirements, status, tests, change record |
| Audit | initialization, migration, consistency review | full `noc_docs/` tree as needed |
| Query | answering docs questions | route through index, then read smallest relevant docs |

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

Default to Small Mode unless evidence supports Domain Mode.

Use Domain Mode when:

- feature count is 20 or more
- domain count is 3 or more
- app/service count is 3 or more
- monorepo is detected
- domain-level guardrails are required

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

The installed Git hook is advisory by default. It should warn when code changes lack staged `noc_docs/` changes, but it must not block commits that intentionally leave docs unchanged.

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

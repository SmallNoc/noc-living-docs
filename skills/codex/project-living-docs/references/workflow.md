# Workflow

## Modes

| Mode | Use When | Read Scope |
|---|---|---|
| Light | narrow bug fix or small implementation | entry file, `docs-map.md`, feature map, affected `agent-guide.md`, `guardrails.md` |
| Deep | new feature, behavior change, refactor, API/data/security/deployment change | Light docs plus `requirements.md`, `status.md`, `test-record.md`, `change-record.md` |
| Audit | initialization, migration, consistency review | full relevant `noc_docs/` tree |
| Query | answering a docs question only | route through index, then read smallest relevant docs |

Escalate Light to Deep when code may change behavior, requirements, tests, security, public API, schema, persistence, permissions, billing, deployment, or cross-feature contracts.

## Read Fallbacks

For each affected feature:

1. Read feature `agent-guide.md` if present.
2. Read feature `guardrails.md` if present.
3. If feature guardrails are missing in domain mode, read `noc_docs/domains/<domain>/guardrails.md`.
4. If feature docs are missing or no feature maps to the changed path, read `noc_docs/docs-map.md`, `noc_docs/project-status.md`, and the closest domain or feature index.
5. If `feature-map.json` has `completeness.complete=false`, missing docs, or stale-looking entries, say so and use Deep or Audit mode.

Do not invent requirements to fill missing docs. Record the gap in `status.md`, `notes.md`, or the final response.

## Development Loop

Before editing code:

1. Identify feature/domain from request, paths, and `feature-map.json`.
2. Run `python scripts/noc.py work <project> --feature <feature> --intent "<intent>"` when scripts are available.
3. Read docs from the work plan.
4. Put confirmed requirement changes in `requirements.md`.
5. Put uncertain discussion in `notes.md`.

After editing code:

1. Update `status.md` when actual behavior changes.
2. Update `requirements.md` only when intended behavior changes.
3. Append `change-record.md` for important changes.
4. Append `test-record.md` with verification commands and results.
5. Update `guardrails.md` only when constraints, compatibility rules, or risks changed.
6. Run `index` after docs, features, domains, or mappings changed.
7. Run `check --staged --warn-only` before commit when Git is available.

## Conflict Handling

- Docs conflict with code: treat code as current behavior and update `status.md`.
- Requirements conflict with code: do not silently rewrite requirements; ask when product intent is unclear.
- User request conflicts with guardrails: stop and ask for explicit confirmation.
- Feature mapping is ambiguous: use `suggest-map` for candidates, but do not write ambiguous mappings.

## CLI Commands

```bash
python scripts/noc.py init /path/to/project
python scripts/noc.py work /path/to/project --feature <feature> --intent "<intent>"
python scripts/noc.py work /path/to/project --path <code/path>
python scripts/noc.py suggest-map /path/to/project
python scripts/noc.py index /path/to/project
python scripts/noc.py check /path/to/project --staged --warn-only
python scripts/noc.py validate --target /path/to/project
```

# Workflow

## Protocol Detection

Read `noc_docs/.living-docs/config.json`. When `protocol_version` is `2` and `layout` is `simplified`, use `routing.json` and the three project-level memory files returned by `noc work`. Otherwise retain the v1 feature/domain workflow below. Never migrate a v1 project implicitly.

For v2, update memory only for durable changes to requirements, behavior, constraints, API, data structures, verification, or project phase. Ordinary bug fixes, formatting, and small refactors do not require documentation changes.

## Semantic Memory Impact

Classify the actual diff, not the size of the task or the amount of work performed:

| Impact | Durable change | v2 update |
|---|---|---|
| `none` | No new fact future Codex sessions require | No project memory file |
| `project` | Goal, phase, major capability, technical boundary, or architecture fact | `project.md` |
| `guardrails` | Security, permission, data-loss, compatibility, public API, migration, or deployment constraint | `guardrails.md` |
| `verification` | Standard test/build/release/acceptance command or durable gate | `verification.md` |

Formatting, comments, local renames, behavior-preserving small refactors, fixes that restore an existing requirement, existing test runs, and ordinary tests use `none`. Multiple durable categories may be declared by repeating `--memory-impact`. Never store temporary execution logs, chat history, ordinary results, or uncertain claims as long-term facts.

## Modes

| Mode | Use When | Read Scope |
|---|---|---|
| Light | narrow bug fix or small implementation | entry file, `docs-map.md`, feature map, affected `agent-guide.md`, `guardrails.md` |
| Deep | new feature, behavior change, refactor, API/data/security/deployment change | Light docs plus `requirements.md`, `status.md`, `test-record.md`, `change-record.md` |
| Audit | initialization, migration, consistency review | full relevant `noc_docs/` tree |
| Query | answering a docs question only | route through index, then read smallest relevant docs |

Escalate Light to Deep when code may change behavior, requirements, tests, security, public API, schema, persistence, permissions, billing, deployment, or cross-feature contracts.

## Read Fallbacks

For simplified v2 projects, read `project.md`, `guardrails.md`, and `verification.md` as the minimum fallback. Do not create feature or area documents merely because routing is broad.

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
2. Run `noc work <project> --path <code/path> --json --intent "<intent>"`. Use `--feature <feature>` when the feature name is clearer than the path.
3. Read docs from the work plan.
4. Put confirmed requirement changes in `requirements.md`.
5. Put uncertain discussion in `notes.md`.

After editing code:

1. Classify the diff using the semantic threshold above.
2. For v2, update only the corresponding project memory files; `none` changes no NOC docs.
3. For v1, preserve the existing document layout but avoid routine churn and update only durable facts.
4. Run `noc check <project> --staged --memory-impact <impact>`, repeating the impact option when needed.

## Conflict Handling

- Docs conflict with code: treat code as current behavior and update `status.md`.
- Requirements conflict with code: do not silently rewrite requirements; ask when product intent is unclear.
- User request conflicts with guardrails: stop and ask for explicit confirmation.
- Feature mapping is ambiguous: use `suggest-map` for candidates, but do not write ambiguous mappings.

## CLI Commands

```bash
noc init /path/to/project
noc work /path/to/project --path <code/path> --json --intent "<intent>"
noc work /path/to/project --feature <feature> --json
noc suggest-map /path/to/project
noc index /path/to/project
noc check /path/to/project --staged --warn-only
noc validate --target /path/to/project
```

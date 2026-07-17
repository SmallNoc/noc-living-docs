# Workflow

## Protocol Detection

Read `noc_docs/.living-docs/config.json` and always start with `noc work <project> --path <code/path> --json --intent "<intent>"` when code may change.

- `protocol_version: 2`, `layout: feature-archive`: use the feature-archive workflow below.
- `protocol_version: 2`, `layout: simplified`: use the three project-level memory files returned by `noc work`.
- v1 `small` or `domain`: retain the v1 feature/domain workflow below.

Do not silently migrate simplified, small, or domain projects. Migration only happens when the user explicitly asks for it.

For v2, update memory only for durable changes to requirements, behavior, constraints, API, data structures, verification, or project phase. Ordinary bug fixes, formatting, and small refactors do not require documentation changes.

## Feature-Archive Workflow

Use this workflow only when `layout` is `feature-archive`.

1. Run `noc work <project> --path <code/path> --json --intent "<intent>"`.
2. Select the feature:
   - high confidence, non-ambiguous candidate: use it automatically.
   - clear new business feature: run `noc feature ensure <project> --id <ascii-kebab-id> --name "<display name>" --json`.
   - ambiguous or low confidence result: ask the user once which feature to use or whether to create one.
3. Read `project.md`, `guardrails.md`, `verification.md`, and `noc_docs/features/<feature-id>/overview.md` before editing code.
4. Change code.
5. Run real, relevant verification. `passed` requires exit_code 0; if verification was not run, record `not_run` or explain why.
6. Run `noc evidence <project> --staged --json` to collect code evidence.
7. Write verification evidence JSON and run `noc evidence record <project> --feature-id <feature-id> --file <evidence.json> --json`.
8. Generate a structured feature patch and run `noc feature update <project> --id <feature-id> --patch-file <patch.json> --json`.
9. Write a feature impact JSON and run `noc check <project> --feature-impact-file <impact.json> --json`.
10. Final response: concise, in the user’s language, with verification and NOC docs changed.

Do not freely rewrite `overview.md`; update it only through `noc feature update`. Do not write unconfirmed user discussion as confirmed requirements. Do not turn plans into current implementation. Do not mark tests passed without real verification. Do not create major changes for ordinary edits.

### Feature-Archive Language

When `language: zh-CN`, keep generated feature prose and final summaries in Simplified Chinese. Preserve explicit Chinese user requirements in `已确认需求`. JSON/YAML keys, feature ids, CLI flags, paths, code identifiers, and commands stay English or original. Never translate an existing Chinese `overview.md` into English.

## Semantic Memory Impact

Classify the actual diff, not the size of the task or the amount of work performed:

| Impact | Durable change | v2 update |
|---|---|---|
| `none` | No new fact future Codex sessions require | No project memory file |
| `project` | Goal, phase, major capability, technical boundary, or architecture fact | `project.md` |
| `guardrails` | Security, permission, data-loss, compatibility, public API, migration, or deployment constraint | `guardrails.md` |
| `verification` | Standard test/build/release/acceptance command or durable gate | `verification.md` |

Formatting, comments, local renames, behavior-preserving small refactors, fixes that restore an existing requirement, existing test runs, and ordinary tests use `none`. Multiple durable categories may be declared by repeating `--memory-impact`. Never store temporary execution logs, chat history, ordinary results, or uncertain claims as long-term facts.

## Read Fallbacks

For simplified v2 projects, read `project.md`, `guardrails.md`, and `verification.md` as the minimum fallback. Do not create feature or area documents merely because routing is broad.

For each affected feature:

1. Read feature `agent-guide.md` if present.
2. Read feature `guardrails.md` if present.
3. If feature guardrails are missing in domain mode, read `noc_docs/domains/<domain>/guardrails.md`.
4. If feature docs are missing or no feature maps to the changed path, read `noc_docs/docs-map.md`, `noc_docs/project-status.md`, and the closest domain or feature index.
5. If `feature-map.json` has `completeness.complete=false`, missing docs, or stale-looking entries, report the limitation and read only the additional relevant v1 documents needed for the task.

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
noc feature ensure /path/to/project --id <feature-id> --name "<name>" --json
noc feature update /path/to/project --id <feature-id> --patch-file <patch.json> --json
noc evidence /path/to/project --staged --json
noc evidence record /path/to/project --feature-id <feature-id> --file <evidence.json> --json
noc check <project> --feature-impact-file <impact.json> --json
noc suggest-map /path/to/project
noc index /path/to/project
noc check /path/to/project --staged --warn-only
noc validate --target /path/to/project
```

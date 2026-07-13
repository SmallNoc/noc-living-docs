---
name: project-living-docs
description: Use for AI-assisted code changes that must keep project living docs in sync. Triggers on feature work, bug fixes, refactors, API/schema/security/deployment changes, requirement updates, tests, guardrails, and change records. Do not use for general Q&A or non-project snippets.
---

# Project Living Docs

Use NOC Living Docs as an agent memory router. Route through `noc_docs/`, read only the affected docs, update only facts that changed, then verify with the CLI.

## Trigger

Use this skill for:

- initializing or migrating `noc_docs/`
- discussing a requirement and then changing code
- new features, bug fixes, refactors, API/data/security/deployment changes
- checking whether code changes need docs updates
- querying or auditing project living docs

Do not use it for general questions that do not involve project memory, code behavior, requirements, guardrails, tests, or NOC documentation.

## Execution

1. Run the work plan first; it identifies either v2 project memory or the affected v1 feature/domain.
2. Run a work plan when code may change:

```bash
noc work /path/to/project --path <code/path> --json --intent "<agreed requirement>"
```

Use `--feature <feature>` when feature names are clearer than paths. Prefer `--json` for machine-readable routing; fall back to the text output only when the installed CLI does not support JSON.

3. Read only the files returned by the work plan. For simplified v2 projects this is normally `project.md`, `guardrails.md`, and `verification.md`; v1 projects keep their feature/domain documents.
4. After changing code, inspect the actual diff and classify its memory impact. Ask: **If the next Codex session did not know this fact, could it make an incorrect change?** Only a clear "yes" belongs in long-term project memory.
5. Change code.
6. Update only the files selected by the impact classification. Never write temporary execution records, chat history, ordinary test results, or implementation narration into long-term memory. Do not turn uncertain content into facts.
7. Run `noc check <project> --memory-impact <impact>` internally, repeating the option for multiple impacts. Do not ask ordinary users to learn or run advanced commands.

## Memory Impact

- `none`: formatting, comment fixes, local renames, behavior-preserving small refactors, implementation bug fixes that restore existing requirements, running existing tests, and ordinary tests added under the existing verification approach. Do not modify `noc_docs/`.
- `project`: project goals, project phase, major capabilities, technical boundaries, or architecture facts changed. In v2, update only `project.md`.
- `guardrails`: durable security, permission, data-loss, compatibility, public API, migration, or deployment constraints changed. In v2, update only `guardrails.md`.
- `verification`: standard test commands, build/release/acceptance procedures, or durable verification gates changed. In v2, update only `verification.md`.

Multiple durable impacts may apply; update only their corresponding files. Do not create `change-record.md`, `test-record.md`, `notes.md`, areas, or any new long-term document type for v2. For v1, keep reading the existing structure but apply the same semantic threshold and avoid routine document churn.

For detailed workflow rules, read `references/workflow.md`.

## Do Not Proceed

Stop and ask the user before editing code when:

- the request conflicts with `guardrails.md` or domain guardrails
- product intent conflicts with `requirements.md` and the intended direction is unclear
- affected feature/domain cannot be identified and the change is not obviously global
- required docs are missing and the task depends on unknown requirements or constraints
- the user asks to silently rewrite requirements to match current code
- the change touches security, permissions, billing, data loss, migrations, or public API contracts and the requested behavior is ambiguous

## Definition Of Done

A task using this skill is done only when:

- affected docs were identified through the v2 routing data or v1 feature map
- required docs were read or missing docs were called out
- code changes and docs changes agree
- `requirements.md` changed only for intended behavior changes
- `status.md` reflects current behavior after code changes
- `test-record.md` records verification or explains why verification was not run
- `change-record.md` records important implementation changes, not routine churn
- indexes/checks were run when available, or skipped with reason

Use a normal final response focused on development and test results. Do not output a fixed NOC template. Only when memory changed, append one short sentence such as `Project memory updated: project.md`.

## References

- `references/workflow.md`: mode selection, fallback rules, conflict handling, work loop
- `references/feature-doc-template.md`: what each feature doc should contain
- `references/domain-mode-guide.md`: when and how to use domain mode
- `references/codex-prompts.md`: recommended user prompts for Codex plan/goal/code workflows

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
4. For v2, update memory only when requirements, behavior, constraints, API, data structure, verification, or project phase creates a fact future sessions need. Routine fixes, formatting, and small refactors require no memory churn.
5. Change code.
6. Update `status.md`, `test-record.md`, `change-record.md`, and `guardrails.md` only when behavior, verification, important changes, or constraints changed.
7. Call internal NOC commands as needed; do not ask ordinary users to learn or run advanced commands.

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

In the final response, mention memory updates only when useful. Do not force a fixed NOC template onto every answer.

## References

- `references/workflow.md`: mode selection, fallback rules, conflict handling, work loop
- `references/feature-doc-template.md`: what each feature doc should contain
- `references/domain-mode-guide.md`: when and how to use domain mode
- `references/codex-prompts.md`: recommended user prompts for Codex plan/goal/code workflows

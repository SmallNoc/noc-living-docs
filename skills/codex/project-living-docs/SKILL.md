---
name: project-living-docs
description: Use when code changes, feature work, refactors, API/schema/security changes, bug fixes, or project initialization need NOC Living Docs kept in sync with requirements, current behavior, guardrails, tests, or change history.
---

# Project Living Docs

Use NOC Living Docs as executable project memory. Route through `noc_docs/`, read only the affected docs, update the living docs when code or intent changes, then verify with the CLI.

## Trigger

Use this skill for:

- initializing or migrating `noc_docs/`
- discussing a requirement and then changing code
- new features, bug fixes, refactors, API/data/security/deployment changes
- checking whether code changes need docs updates
- querying or auditing project living docs

Do not use it for general questions that do not involve project memory, code behavior, requirements, guardrails, tests, or NOC documentation.

## Execution

1. Identify affected feature/domain from the request, changed paths, and `noc_docs/.living-docs/feature-map.json`.
2. Run a work plan when code may change:

```bash
python scripts/noc.py work /path/to/project --feature <feature> --intent "<agreed requirement>"
```

Use `--path <code/path>` when paths are clearer than feature names.

3. Read the smallest relevant docs: `agent-guide.md`, `requirements.md`, `status.md`, `guardrails.md`, `test-record.md`, plus domain guardrails when present.
4. Write confirmed new/changed intent to `requirements.md`; put uncertain discussion in `notes.md`.
5. Change code.
6. Update `status.md`, `test-record.md`, `change-record.md`, and `guardrails.md` when behavior, verification, important changes, or constraints changed.
7. Run `python scripts/noc.py index <project>` after docs, feature, or mapping changes.
8. Run `python scripts/noc.py check <project> --staged --warn-only` before commit when Git is available.

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

- affected docs were identified through feature map, paths, or explicit feature name
- required docs were read or missing docs were called out
- code changes and docs changes agree
- `requirements.md` changed only for intended behavior changes
- `status.md` reflects current behavior after code changes
- `test-record.md` records verification or explains why verification was not run
- `change-record.md` records important implementation changes
- indexes/checks were run when available, or skipped with reason

## Final Response Format

End with:

```text
NOC Living Docs:
- docs checked:
- docs updated:
- docs intentionally unchanged:
- commands run:
- tests run:
- remaining risks:
```

Keep the lists short. Use `none` when a category does not apply.

## References

- `references/workflow.md`: mode selection, fallback rules, conflict handling, work loop
- `references/feature-doc-template.md`: what each feature doc should contain
- `references/domain-mode-guide.md`: when and how to use domain mode
- `references/codex-prompts.md`: recommended user prompts for Codex plan/goal/code workflows

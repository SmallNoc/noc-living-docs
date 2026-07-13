# Token Policy

NOC Living Docs is designed for deterministic routing, not full-context loading.

## Route First

Run `noc work <project> --path <code/path> --json` before changing code and read only the files returned by the work plan.

New projects use v2 simplified by default. Their long-term project memory is limited to:

- `noc_docs/project.md`
- `noc_docs/guardrails.md`
- `noc_docs/verification.md`

Do not create feature, domain, requirements, status, test-record, change-record, or notes documents for v2 projects.

## Memory Impact

After changing code, classify the actual diff rather than the task size:

- `none`: no durable fact for a future session; update no long-term memory.
- `project`: update `project.md` only.
- `guardrails`: update `guardrails.md` only.
- `verification`: update `verification.md` only.

Multiple durable impacts may apply. Ordinary formatting, local renames, behavior-preserving refactors, fixes that restore existing requirements, existing test runs, and ordinary tests use `none`.

## Legacy v1 Compatibility

Existing v1 feature/domain projects remain supported and are never migrated implicitly. When `noc work --json` reports a v1 project, follow the returned feature/domain routing and read only the relevant legacy documents.

## Routing Data

Use `.living-docs/` files as routing indexes and generated metadata. Do not treat them as the source of truth when they conflict with actual documentation or code.

# Agent Protocol

<!-- noc-living-docs:start -->

## NOC Living Docs

This project uses `noc_docs/` as the only living documentation root.

Do not create `docs/` for this protocol. Do not move living documentation outside `noc_docs/`.

### Before Modifying Code

1. Read `noc_docs/docs-map.md`.
2. When the CLI is available, run `noc work <project> --path <code/path> --json` for the planned or changed path. Use `--feature <feature>` when the feature name is clearer than the path.
3. Identify the affected feature or domain from the work plan.
4. Read the affected feature's `agent-guide.md` and `guardrails.md`.
5. Read `requirements.md`, `status.md`, and `test-record.md` when the change affects behavior, requirements, or verification.
6. Follow `noc_docs/development/git-workflow.md` and `noc_docs/development/testing.md`.

### After Modifying Code

1. Update `status.md` when actual behavior changes.
2. Update `requirements.md` only when intended behavior changes.
3. Append `change-record.md` for important modifications.
4. Append `test-record.md` with verification results.
5. Update indexes when features or domains change.
6. Report which NOC docs were checked or updated.

### Guardrails

Treat `guardrails.md` as hard constraints. If the requested change conflicts with a forbidden item, stop and ask the user before editing code.

<!-- noc-living-docs:end -->

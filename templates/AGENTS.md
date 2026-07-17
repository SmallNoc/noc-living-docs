# Agent Protocol

<!-- noc-living-docs:start -->

## NOC Living Docs

This project uses `noc_docs/` as the only living documentation root and NOC as an agent memory router.

Do not create `docs/` for this protocol. Do not move living documentation outside `noc_docs/`.

### Before Modifying Code

1. Read `noc_docs/docs-map.md`.
2. When the CLI is available, run `noc work <project> --path <code/path> --json` for the planned or changed path. Use `--staged` or `--changed` when the Git diff is the clearest input. Use `--feature <feature>` when the feature name is clearer than the path.
3. Identify the layout and affected memory from the work plan. In feature-archive projects, high-confidence candidates may be used automatically; ambiguous candidates should be clarified once.
4. Read only the affected docs listed in the work plan. In feature-archive projects this includes project memory and the selected `overview.md`; in v1 projects this may include `agent-guide.md` and `guardrails.md`.
5. Read requirements, status, and verification records only when the change affects intent, behavior, or verification.
6. Old layouts are not migrated unless the user explicitly asks. Do not silently convert simplified, small, or domain projects to feature-archive.
7. Follow `noc_docs/development/git-workflow.md` and `noc_docs/development/testing.md` when those files exist.

### After Modifying Code

1. For feature-archive projects, update feature facts only through structured CLI commands such as `noc feature update`; do not freely rewrite `overview.md`.
2. Record verification as passed only after a real command ran and returned exit code 0.
3. For simplified projects, update only the routed project-level memory files when future sessions need the fact.
4. For v1 projects, update `requirements.md`, `status.md`, `test-record.md`, and `change-record.md` only when their existing meanings apply.
5. Do not churn docs that did not materially change.
6. Report which NOC docs were checked or updated.

### Guardrails

Treat `guardrails.md` as hard constraints. If the requested change conflicts with a forbidden item, stop and ask the user before editing code.

<!-- noc-living-docs:end -->

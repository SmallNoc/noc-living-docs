# Docs Map

## Current Protocol

New projects use v2 simplified by default. Run `noc work <project> --path <code/path> --json` and read the routed project memory:

- `noc_docs/project.md`
- `noc_docs/guardrails.md`
- `noc_docs/verification.md`

After a change, classify the actual diff by memory impact: `none`, `project`, `guardrails`, or `verification`. Update only the corresponding long-term memory file; `none` requires no memory update.

The feature/domain layout below is retained only for legacy v1 compatibility. Existing v1 projects are not migrated implicitly.

## Legacy v1 Routing Table

| Situation | Read |
|---|---|
| Any code change | `AGENTS.md`, `noc_docs/project-status.md` |
| Feature change | affected feature `agent-guide.md`, `guardrails.md` |
| Requirement change | affected feature `requirements.md` |
| Behavior change | affected feature `status.md` |
| Test or verification change | affected feature `test-record.md`, `noc_docs/development/testing.md` |
| Git commit | `noc_docs/development/git-workflow.md` |
| Documentation uncertainty | `noc_docs/development/documentation-policy.md` |

Use the v1 table only after `noc work --json` reports a v1 feature/domain project.


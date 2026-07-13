# Docs Map

## Current Protocol

New projects use v2 simplified by default and store long-term memory in `project.md`, `guardrails.md`, and `verification.md`. Run `noc work <project> --path <code/path> --json` for routing, then use memory impact to decide whether any long-term memory changes.

This example demonstrates the explicitly selected legacy v1 domain layout. Existing v1 projects remain supported and are not migrated implicitly.

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

Use this table only after `noc work --json` reports a v1 domain project.


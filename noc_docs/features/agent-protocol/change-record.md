# Change Record: agent-protocol

## 2026-07-14 - Support simplified project memory

- Added a concise v2 managed block while retaining the legacy template for v1 projects.
- Updated both packaged Skill copies to route v2 through project-level memory and avoid routine documentation churn.
- Removed the mandatory fixed final-response template from the Skill.

## 2026-07-13 - Standardize installed CLI usage

- Verified the canonical AGENTS template already uses `noc` commands.
- Kept the managed block and v1 documentation workflow unchanged while aligning installed-user guidance with `noc setup`.

## 2026-07-08 - Prefer JSON work plans in agent entry

### Reason

Agents need a deterministic first step before reading broader project context.

### Changed

- `templates/AGENTS.md` and generated `AGENTS.md` now instruct agents to run `noc work <project> --path <code/path> --json` when the CLI is available.

### Impact

- Agents can route through NOC with less free-text interpretation.

## 2026-07-08 - Reframe protocol as route-first memory

### Reason

NOC should stay small and hard: route agents to the right project memory, not imply that every task requires a full documentation ritual.

### Changed

- `templates/AGENTS.md` and generated `AGENTS.md` now describe NOC as an agent memory router.
- The before-code steps say to read only docs listed in the work plan.
- The after-code steps say not to churn docs that did not materially change.

### Impact

- Agents get clearer permission to keep context narrow.
- The protocol better matches the product goal of preventing context drift without becoming a documentation platform.


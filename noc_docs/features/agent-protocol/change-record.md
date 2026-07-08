# Change Record: agent-protocol

## 2026-07-08 - Prefer JSON work plans in agent entry

### Reason

Agents need a deterministic first step before reading broader project context.

### Changed

- `templates/AGENTS.md` and generated `AGENTS.md` now instruct agents to run `noc work <project> --path <code/path> --json` when the CLI is available.

### Impact

- Agents can route through NOC with less free-text interpretation.


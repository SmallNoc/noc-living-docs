# Agent Compatibility

NOC Living Docs is a protocol plus CLI. Agent-specific files are entry points into the same protocol, not separate sources of truth.

## Compatibility Matrix

| Agent surface | Entry point | Status | Notes |
|---|---|---|---|
| Codex | `skills/codex/project-living-docs/SKILL.md` | Primary | Full Light / Deep / Audit / Query workflow is documented in the skill. |
| Generic agents | `AGENTS.md` managed block | Supported | Canonical project-level managed block. Used by `init --agent-file AGENTS.md`. |
| Claude Code | `CLAUDE.md` template | Basic | Points to the canonical `AGENTS.md` protocol. Needs real Claude Code dogfood before v1. |
| Gemini CLI | `GEMINI.md` template | Basic | Points to the canonical `AGENTS.md` protocol. Needs real Gemini CLI dogfood before v1. |

## Compatibility Rules

- `templates/AGENTS.md` is the canonical managed block for project entry files.
- `templates/CLAUDE.md` and `templates/GEMINI.md` must remain consistent with the canonical protocol.
- Agent entry files must preserve user-authored rules outside the NOC managed block.
- Agent integrations should call the CLI for deterministic work: `init`, `index`, `validate`, `check`, `hook`, and `suggest-map`.

## v1 Requirement

Before v1, run at least one dogfood pass for each target surface that claims more than basic support:

- Codex skill execution on a real code change.
- Generic `AGENTS.md` flow on a project with existing rules.
- Claude Code or Gemini CLI flow if they are advertised as supported beyond template-level compatibility.

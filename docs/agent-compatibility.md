# Agent Compatibility

NOC Living Docs is a protocol plus CLI. Agent-specific files are entry points into the same protocol, not separate sources of truth.

## Compatibility Matrix

| Agent surface | Entry point | Status | Notes |
|---|---|---|---|
| Codex | Installed `project-living-docs` Skill | Formally supported | `noc setup` installs the bundled Skill version that matches the CLI. Setup and isolated installation behavior are covered by repository tests. |
| Generic agents | `AGENTS.md` managed block | Basic protocol support | `noc init` adds the canonical managed block while preserving user-authored content outside it. |
| Claude Code | `CLAUDE.md` template | Template-level basic compatibility | The template points to the shared protocol. The repository does not claim complete Claude Code runtime validation. |
| Gemini CLI | `GEMINI.md` template | Template-level basic compatibility | The template points to the shared protocol. The repository does not claim complete Gemini CLI runtime validation. |

## Compatibility Rules

- `templates/AGENTS.md` is the canonical managed block for project entry files.
- `templates/CLAUDE.md` and `templates/GEMINI.md` must remain consistent with the canonical protocol.
- Agent entry files must preserve user-authored rules outside the NOC managed block.
- Codex uses `noc work --json` for deterministic routing and applies the v2 simplified or v1 legacy rules selected by project configuration.
- Template availability alone is not evidence of full runtime support; compatibility claims must stay at the level demonstrated by implementation and tests.

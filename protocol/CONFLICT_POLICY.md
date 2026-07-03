# Conflict Policy

Conflicts must be surfaced, not hidden.

## Documentation vs Code

When `status.md` conflicts with code:

- Treat code as the best evidence of current behavior.
- Update `status.md` if the current behavior is clear.
- Add a note to `notes.md` when behavior is ambiguous.

## Requirements vs Code

When `requirements.md` conflicts with code:

- Do not silently change requirements to match code.
- If the task is to fix implementation, follow requirements.
- If the task is to document reality, update `status.md` and record the mismatch in `notes.md`.
- Ask the user when intent is unclear.

## Guardrails vs User Request

When a user request conflicts with `guardrails.md`:

- Stop before editing code.
- Explain the conflict.
- Ask for explicit confirmation or a guardrail update.

## Existing Agent Files

Never overwrite existing `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`.

Append managed blocks with markers:

```md
<!-- noc-living-docs:start -->
...
<!-- noc-living-docs:end -->
```


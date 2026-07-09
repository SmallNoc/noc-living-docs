# Feature Doc Template

Use these files under `noc_docs/features/<feature>/` or `noc_docs/domains/<domain>/features/<feature>/`.

## agent-guide.md

Purpose: tell an agent where to start.

Include:

- related code paths
- docs to read before changing the feature
- common commands
- local conventions and known traps

## requirements.md

Purpose: describe intended behavior.

Include:

- user-visible behavior
- business rules
- API or UI contract expectations
- acceptance criteria
- open requirement questions

Do not rewrite this file just to match current code. If code differs from intent, update `status.md` and ask whether to fix code or change the requirement.

## status.md

Purpose: describe current implemented behavior.

Include:

- what exists now
- known gaps from requirements
- current limitations
- compatibility notes
- important implementation facts

## guardrails.md

Purpose: describe constraints that must not be broken.

Include:

- security and permission boundaries
- data integrity rules
- public API compatibility rules
- migration and rollback constraints
- performance or operational limits

## test-record.md

Purpose: record verification history.

Include:

- command run
- result
- date or context
- what was not tested
- residual risk

## change-record.md

Purpose: record important changes and why they happened.

Include:

- short summary
- reason
- affected files or modules
- docs updated
- follow-up risks

## notes.md

Purpose: hold informal information that is not yet a requirement or status.

Use for:

- uncertain discussion
- research notes
- ideas not yet accepted
- questions for the user

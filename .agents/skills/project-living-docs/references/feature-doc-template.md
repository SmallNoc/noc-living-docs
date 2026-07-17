# Feature Doc Template

For feature-archive projects, each feature uses one `noc_docs/features/<feature-id>/overview.md`. Do not freely rewrite `overview.md`; update managed facts through `noc feature update` with a structured patch.

## feature-archive overview.md

Purpose: hold the feature’s durable goal, confirmed requirements, current implementation, constraints, code scope, verification method, recent verification results, major changes, and pending questions.

Rules:

- `id` is a stable ASCII kebab-case feature id.
- `name` may be Chinese, for example `用户登录`.
- When `language: zh-CN`, section prose stays Simplified Chinese.
- Requirements become confirmed only when the user explicitly confirmed them.
- Verification results may say `passed` only after a real command ran and returned exit code 0.
- Keep JSON/YAML keys, feature ids, CLI flags, paths, code identifiers, and commands English or original.

Use the files below only for v1 small/domain compatibility under `noc_docs/features/<feature>/` or `noc_docs/domains/<domain>/features/<feature>/`.

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

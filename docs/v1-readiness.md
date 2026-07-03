# v1 Readiness

NOC Living Docs v1 should stay small and hard. The core promise is:

> Help AI coding agents read the right project context before changes, update the right living docs after changes, and verify that docs and code did not drift.

## In Scope

- Fixed `noc_docs/` protocol root.
- Small and Domain layouts.
- Agent entry managed blocks.
- CLI commands: `init`, `index`, `validate`, `check`, `hook`, `suggest-map`.
- Advisory pre-commit hook.
- Feature map routing and trust signals.
- Feature map suggestions with optional non-overwriting writes.
- Lightweight change hints.
- Release/version/changelog guardrails.
- Migration reports for real-project dogfood.

## Out of Scope for v1

- Dashboard or server.
- Full static analysis.
- Blocking policy by default.
- Project management workflows.
- Replacing external docs, issue trackers, ADR systems, or release platforms.
- One-command destructive repair or migration.

## v1 Gate

- At least 3 migration reports:
  - one small project,
  - one project with existing `docs/` and agent rules,
  - one monorepo or multi-service project.
- Full local validation passes:
  - `python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py`
  - `python scripts/release.py --check`
  - `python scripts/noc.py validate`
  - `python -m unittest tests.test_noc_cli tests.test_release_cli`
- README documents the minimal workflow.
- `CHANGELOG.md` has a non-placeholder v1 entry.
- `VERSION` and Git tag match.

## Current Status

The repository has four dogfood reports:

- `docs/migration-reports/2026-07-04-noc-living-docs.md`
- `docs/migration-reports/2026-07-04-myspringboot.md`
- `docs/migration-reports/2026-07-04-edm-ui.md`
- `docs/migration-reports/2026-07-04-edmpro3.md`

This satisfies the small-project, existing-agent project, modular frontend, and multi-project workspace coverage.

`docs/v1-manual-dogfood.md` records the required user input, safety rules, commands, and acceptance criteria for future dogfood runs.

The remaining work before an actual v1 release is release bookkeeping: move the relevant `CHANGELOG.md` notes into a `1.0.0` entry, update `VERSION`, run the release checks, create the Git tag, and push.

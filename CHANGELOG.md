# Changelog

## Unreleased

### Changed

- Added PyPI publishing readiness: modern package metadata, release documentation, Trusted Publishing GitHub Actions workflow, build artifact ignores, and wheel/package-data validation.
- Added the standard `.agents/skills/project-living-docs/` Codex skill path while keeping the legacy `skills/codex/project-living-docs/` path for compatibility.
- Clarified README installation guidance to recommend `pipx install git+https://github.com/SmallNoc/noc-living-docs.git` until PyPI publishing is available.
- Updated README positioning, Codex skill install instructions, GitHub topic suggestions, and skill trigger description.
- Synchronized `pyproject.toml` package version with `VERSION`, `README.md`, and `CHANGELOG.md` at `1.0.1`.
- Expanded README into a bilingual usage guide with aligned English and Chinese sections for install, update, daily use, commands, generated documents, file responsibilities, machine files, and domain mode.

## [1.0.1] - 2026-07-08

### Changed

- Tightened `noc work --json` into a stable agent routing contract with schema version, resolution status, match metadata, confidence, and next actions for unresolved paths.
- Added `noc work --changed --json` and `noc work --staged --json` so agents can route directly from Git diff state.
- Reframed README and agent guidance around NOC as an agent memory router, with a concrete JSON example, quick start, workflow, and comparison table.
- Reworked the Chinese README introduction to explain the project in user-facing terms, including generated document structure, file responsibilities, JSON index roles, token impact, install, update, usage, and uninstall instructions.
- Synchronized the English README with the clearer user-facing structure, including generated docs layout, Markdown/JSON file roles, token cost, install, update, usage, and uninstall instructions.
- Added a `noc.py work` command and skill guidance for turning discussed requirements into a docs checklist before code changes.
- Reworked the Codex skill into a concise executable workflow with Definition of Done, stop conditions, final response format, references, and trigger eval prompts.


## [1.0.0] - 2026-07-04

### Added

- Added `noc.py suggest-map` to print candidate feature path mappings without modifying project files.
- Added `noc.py suggest-map --write` to merge mapping suggestions into `feature-map.json` without overwriting existing paths.
- Added lightweight change hints in `noc.py check` for schema, deployment, CI, security, and API-looking changes.
- Added top-level project directory detection for multi-project workspaces without standard monorepo marker files.
- Added EDMPro3 multi-project dogfood report.


## [0.5.0] - 2026-07-04

### Added

- Added `VERSION` and `scripts/release.py` for repeatable release checks and version bumps.
- Added release preparation support that moves `Unreleased` changelog notes into a target version.
- Added migration tests for existing agent files, existing `docs/`, monorepo domain detection, and config-heavy projects.
- Added a migration report template for real-project dogfood runs.
- Added CI coverage for release checks and release CLI tests.
- Added Tcl and SKILL files to documentation sync checks; Java and Go coverage is now explicit in tests.


## [0.4.0] - 2026-07-04

### Added

- Added feature documentation trust signals in `feature-map.json`, including freshness and completeness metadata.
- Added related-document checking so mapped code changes must be paired with docs for the affected feature.
- Added broader engineering file detection for config, SQL, shell, Dockerfile, and related project files.
- Added regression tests for related docs checks and feature index trust signals.

### Changed

- Reworked the Codex skill instructions into a clearer execution loop with mode selection and fallback rules.
- Updated README command documentation for the stronger `check` behavior and index metadata.

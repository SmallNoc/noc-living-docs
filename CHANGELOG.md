# Changelog

## Unreleased

### Changed

- Reworked the Chinese README introduction to explain the project in user-facing terms, including generated document structure, file responsibilities, JSON index roles, token impact, install, update, usage, and uninstall instructions.
- Synchronized the English README with the clearer user-facing structure, including generated docs layout, Markdown/JSON file roles, token cost, install, update, usage, and uninstall instructions.

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

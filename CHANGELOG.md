# Changelog

## Unreleased

## [1.2.0] - Unreleased

### Added

- New projects now default to simplified protocol v2 project memory.
- `noc init` now completes Skill readiness checks, project detection, initialization, indexing, and health validation in one operation.
- Added semantic memory-impact classification for `none`, `project`, `guardrails`, and `verification`.
- Added repeatable `noc check --memory-impact` declarations with stable JSON results for Skill automation.

### Changed

- Reduced the default new-project structure to `project.md`, `guardrails.md`, `verification.md`, and the machine-managed config, routing, and manifest files.
- Added minimum protocol v2 support to `validate`, `doctor`, `index`, `work`, and `check`.
- Simplified the generated AGENTS managed block so normal users do not need to learn advanced NOC commands.
- Kept existing protocol v1 projects and commands compatible without automatic migration or document deletion.
- Stopped requiring project-memory updates for ordinary Bug fixes, formatting, local renames, behavior-preserving small refactors, and routine tests.
- Removed the fixed NOC Living Docs final-response template; memory updates now use only an optional short summary.

## [1.1.0] - 2026-07-13

### Added

- Added `noc setup`, `noc setup --check`, `noc setup --repair`, and `noc setup --json` as the Codex Skill installation and diagnostics entry points.
- Included the complete `project-living-docs` Skill and its runtime references in the wheel.

### Changed

- Added automatic same-version Skill installation and CLI/Skill version validation, with support for custom `CODEX_HOME` and Codex's default home directory.
- Protected user-maintained Skills with the same name; only NOC-managed installations may be upgraded or repaired.
- Made managed Skill replacement atomic, with rollback on failure and cleanup of files removed by newer versions.
- Stabilized setup JSON fields, error codes, exit codes, and actionable next-step output.
- Updated the installed Skill and user-facing templates to invoke `noc` instead of depending on the source-only `python scripts/noc.py` path.
- Released these installation improvements as a backward-compatible minor release; existing CLI commands and the v1.0.2 document protocol remain supported.

## [1.0.2] - 2026-07-10

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

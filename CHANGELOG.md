# Changelog

## [0.4.0] - 2026-07-04

### Added

- Added feature documentation trust signals in `feature-map.json`, including freshness and completeness metadata.
- Added related-document checking so mapped code changes must be paired with docs for the affected feature.
- Added broader engineering file detection for config, SQL, shell, Dockerfile, and related project files.
- Added regression tests for related docs checks and feature index trust signals.

### Changed

- Reworked the Codex skill instructions into a clearer execution loop with mode selection and fallback rules.
- Updated README command documentation for the stronger `check` behavior and index metadata.

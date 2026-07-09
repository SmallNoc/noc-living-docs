# Change Record: release-quality

## 2026-07-10 - Bump PyPI release target to 1.0.2

### Reason

The local `v1.0.1` tag already exists and points at an older release commit, so the PyPI publishing work needs a new tag instead of rewriting the existing tag.

### Changed

- Bumped `VERSION`, `pyproject.toml`, README current-version text, and release examples to `1.0.2`.
- Moved unreleased changelog notes into a `1.0.2` release entry.

### Impact

- Release bookkeeping can create and push `v1.0.2` without rewriting the existing `v1.0.1` tag.

## 2026-07-10 - Add PyPI publishing readiness

### Reason

The project needs to publish a real `noc-living-docs` package to PyPI so users can install the CLI with `pipx install noc-living-docs` after release.

### Changed

- Updated `pyproject.toml` for modern license metadata, project URLs, explicit package discovery, and package data that includes hidden `.living-docs` template JSON files without pycache files.
- Added `.github/workflows/publish.yml` for tag-triggered PyPI publishing through Trusted Publishing and OIDC.
- Added `docs/release.md` with local build/twine/test checks and manual PyPI Trusted Publishing setup steps.
- Extended `scripts/release.py --check` to verify `pyproject.toml` and README version consistency.
- Added tests for package metadata, publish workflow requirements, release docs, and version mismatch failures.
- Ignored local build artifacts in `.gitignore`.

### Impact

- Maintainers can build and verify PyPI artifacts locally, then publish from a `v*` tag without storing PyPI credentials in the repository.

## 2026-07-09 - Standardize install guidance and version metadata

### Reason

The README pointed users at package install commands that may fail before PyPI publication, and `pyproject.toml` still declared `1.0.0` while other release files declared `1.0.1`.

### Changed

- Updated README English and Chinese install guidance to recommend `pipx install git+https://github.com/SmallNoc/noc-living-docs.git` until PyPI publishing is available.
- Added project-level and global Codex skill copy instructions for `.agents/skills/project-living-docs/`.
- Added GitHub topic suggestions and clearer first-sentence positioning.
- Bumped `pyproject.toml` to `1.0.1` and expanded package keywords.

### Impact

- New users get a currently usable install command, Codex users can find the standard skill path, and release metadata is consistent.

## 2026-07-08 - Cover agent-first work plan behavior

### Reason

Structured work output and agent entry guidance are core usability behavior and should be regression-tested.

### Changed

- Added unittest coverage for `work --json`.
- Added unittest coverage that agent entry and Codex skill prefer JSON work plans.

### Impact

- Future changes are less likely to remove the agent-first path accidentally.

## 2026-07-08 - Strengthen README product entry

### Reason

The previous README preserved the small agent memory router framing but was too sparse to explain the problem, show the workflow, or build confidence for new users.

### Changed

- Expanded README with problem framing, a JSON work-plan example, quick start, agent workflow, comparison table, and coding-agent guidance.
- Added `README.md` to the release-quality feature mapping so future README edits route to a concrete feature.

### Impact

- New users can understand both the product value and the exact command loop without reading deeper docs first.

## 2026-07-08 - Prepare 1.0.1 release

### Reason

The agent-usability work needs to become the version published from `main`, with a new tag instead of moving the existing `v1.0.0` tag.

### Changed

- Bumped `VERSION` to `1.0.1`.
- Updated `CHANGELOG.md` with the agent routing and README improvements.

### Impact

- Release bookkeeping can create a new `v1.0.1` tag without rewriting prior tags.

## 2026-07-08 - Expand bilingual README usage guide

### Reason

The README still under-explained update flow, command coverage, generated document structure, and file responsibilities. The English and Chinese sections also needed to stay structurally aligned.

### Changed

- Expanded README with install, update, quick start, daily use, agent workflow, commands, generated documents, document responsibilities, machine files, domain mode, comparisons, and agent usage.
- Mirrored the same structure in Chinese.
- Corrected the displayed current version to `1.0.1`.

### Impact

- New users can understand how to install, update, initialize, use, and maintain NOC without jumping into deeper docs first.


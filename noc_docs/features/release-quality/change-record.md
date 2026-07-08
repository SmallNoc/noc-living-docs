# Change Record: release-quality

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


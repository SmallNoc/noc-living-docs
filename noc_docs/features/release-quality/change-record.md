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


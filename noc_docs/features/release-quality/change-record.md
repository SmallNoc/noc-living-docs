# Change Record: release-quality

## 2026-07-08 - Cover agent-first work plan behavior

### Reason

Structured work output and agent entry guidance are core usability behavior and should be regression-tested.

### Changed

- Added unittest coverage for `work --json`.
- Added unittest coverage that agent entry and Codex skill prefer JSON work plans.

### Impact

- Future changes are less likely to remove the agent-first path accidentally.


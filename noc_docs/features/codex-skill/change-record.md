# Change Record: codex-skill

## 2026-07-09 - Add standard Codex skill path

### Reason

Codex users need a standard `.agents/skills/project-living-docs/` directory they can copy into a project or global skill folder without guessing from the legacy repo layout.

### Changed

- Added `.agents/skills/project-living-docs/` with the same `SKILL.md`, references, and evals as the legacy `skills/codex/project-living-docs/` path.
- Updated the skill description to front-load AI-assisted code change and living docs synchronization trigger keywords.
- Added regression coverage for both skill paths.

### Impact

- New Codex users can copy the standard skill path while existing users of `skills/codex/project-living-docs/` remain compatible.

## 2026-07-08 - Prefer machine-readable work plans

### Reason

Codex 使用结构化 work plan 比解析自由文本更稳定，能更容易定位需要读取和更新的 NOC 文档。

### Changed

- Codex skill 的执行步骤改为优先运行 `work ... --json`。
- 明确 JSON 不可用时才 fallback 到文本输出。

### Impact

- Codex 和 CLI 的 agent-first 路由方式保持一致。


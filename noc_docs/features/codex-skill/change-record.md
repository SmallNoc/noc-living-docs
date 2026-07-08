# Change Record: codex-skill

## 2026-07-08 - Prefer machine-readable work plans

### Reason

Codex 使用结构化 work plan 比解析自由文本更稳定，能更容易定位需要读取和更新的 NOC 文档。

### Changed

- Codex skill 的执行步骤改为优先运行 `work ... --json`。
- 明确 JSON 不可用时才 fallback 到文本输出。

### Impact

- Codex 和 CLI 的 agent-first 路由方式保持一致。


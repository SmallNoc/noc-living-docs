# Change Record: cli-core

## 2026-07-08 - Add machine-readable work plans

### Reason

Codex 和其他 agent 需要稳定读取“该读哪些文档、该更新哪些文档、最后跑哪些命令”，自由文本不适合作为自动化接口。

### Changed

- `noc work` 增加 `--json`。
- 抽出 work plan 构建逻辑，让文本输出和 JSON 输出共用同一份数据。
- 增加 unittest 覆盖 JSON 输出和旧文本输出兼容性。

### Impact

- agent 可以直接解析 work plan。
- 人类默认使用方式不变。

## 2026-07-08 - Tighten work plan routing contract

### Reason

NOC 的核心目标是作为 agent memory router，而不是让 agent 自己猜路径、解析自由文本或在低置信度场景继续误判。

### Changed

- `work --json` 增加 `schema_version`、`resolution_status`、匹配原因、匹配路径、匹配 pattern 和置信度。
- missing feature 和 unresolved path 会返回明确状态和 `next_actions`。
- `work` 增加 `--changed` 和 `--staged`，可直接从 Git diff 收集路径。

### Impact

- agent 可以区分 resolved、unresolved 和 missing feature。
- 常见工作流可以直接用 Git diff 路由，不需要 agent 自己拼 `--path` 参数。

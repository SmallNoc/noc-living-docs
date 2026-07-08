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

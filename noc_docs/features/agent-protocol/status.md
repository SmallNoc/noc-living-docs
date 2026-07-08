---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: agent-protocol

## Current Behavior

通用 agent 模板现在在改代码前明确建议使用 `noc work <project> --path <code/path> --json`，也允许在 Git diff 更清晰时使用 `--changed` 或 `--staged`。当前仓库的 `AGENTS.md` 已由模板生成并同步了同样规则。协议强调 NOC 是 agent memory router：只读 work plan 列出的相关文档，并只在事实、意图、验证或约束实际变化时更新文档。

## Important Files

- `templates/AGENTS.md`
- `templates/CLAUDE.md`
- `templates/GEMINI.md`
- `AGENTS.md`
- `protocol/`

## Data, API, or Configuration

- managed block 标记：`<!-- noc-living-docs:start -->` / `<!-- noc-living-docs:end -->`
- canonical 通用入口：`templates/AGENTS.md`

## Known Issues

- Claude/Gemini 目前是基础模板，主要指向 canonical AGENTS protocol。


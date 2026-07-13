---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: agent-protocol

## Current Behavior

新建 v2 项目的 managed block 只要求通过 `noc work` 读取最小记忆，并仅在未来会话必须知道新事实时更新记录；普通修复、格式化和小型重构不强制更新。正式 Skill 可检测 v2 简化布局，同时保留现有 v1 文档维护协议，并不再强制固定的 NOC 最终回答模板。

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


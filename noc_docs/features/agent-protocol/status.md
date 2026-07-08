---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: agent-protocol

## Current Behavior

通用 agent 模板现在在改代码前明确建议使用 `noc work <project> --path <code/path> --json`。当前仓库的 `AGENTS.md` 已由模板生成并同步了同样规则。

## Important Files

- `templates/AGENTS.md`
- `templates/CLAUDE.md`
- `templates/GEMINI.md`
- `AGENTS.md`
- `protocol/`

## Data, API, or Configuration

- managed block 标记：`<!-- noc-living-docs:start -->` / `<!-- noc-living-docs:end -->`

## Known Issues

- Claude/Gemini 目前是基础模板，主要指向 canonical AGENTS protocol。


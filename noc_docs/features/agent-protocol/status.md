---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: agent-protocol

## Current Behavior

通用 agent 模板和当前仓库 `AGENTS.md` 使用已安装的 `noc` 命令，不依赖仓库内脚本路径。模板在改代码前明确建议使用 `noc work <project> --path <code/path> --json`，也允许在 Git diff 更清晰时使用 `--changed` 或 `--staged`。现有 v1 文档维护协议保持不变。

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


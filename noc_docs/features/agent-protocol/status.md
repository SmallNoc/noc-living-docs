---
status: active
last_reviewed: 2026-07-17
source_of_truth: code
confidence: medium
---

# Current Status: agent-protocol

## Current Behavior

新建 v2 项目的 managed block 只要求通过 `noc work` 读取最小记忆，并仅在未来会话必须知道新事实时更新记录；普通修复、格式化和小型重构不强制更新。正式 Skill 可检测 v2 简化布局，同时保留现有 v1 文档维护协议，并不再强制固定的 NOC 最终回答模板。

两套正式 Skill 现在根据实际 diff 声明 none/project/guardrails/verification；格式化、局部重命名、行为不变重构、恢复既有要求的 Bug 修复和普通测试均为 none。长期影响只更新对应 v2 文件，v1 继续读取旧结构但使用相同的语义阈值。

现行 docs map、Skill workflow reference 和 token policy 已统一采用 route-first 规则：默认 v2 simplified 通过 `noc work --json` 路由三份项目记忆，再按 memory impact 判断是否更新；feature/domain 仅作为 legacy v1 compatibility。

阶段 7 后，canonical `templates/AGENTS.md` 兼容 feature-archive：改代码前通过 `noc work --json` 识别 layout 和相关 memory，高置信度 feature 候选可自动使用，歧义候选只澄清一次；改代码后 feature-archive 使用结构化 CLI 更新，simplified 仍保持项目级三文件流程，small/domain 继续作为旧布局兼容且不会静默迁移。

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


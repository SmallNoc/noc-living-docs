---
status: active
last_reviewed: 2026-07-08
source_of_truth: product-intent
confidence: medium
---

# Requirements: agent-protocol

## Summary

agent 协议应该让不同工具用同一套 `noc_docs/` 规则工作，并优先通过 CLI work plan 缩小阅读范围。

## Business Rules

- BR-001: `templates/AGENTS.md` 是 managed block 的 canonical source。
- BR-002: agent 改代码前应优先运行 `noc work <project> --path <code/path> --json`。
- BR-003: agent 应只读 work plan 路由出的最小相关文档，避免把 NOC 当成全量文档平台。

## Acceptance Criteria

- Simplified v2 AGENTS blocks stay short, route through `noc work`, and do not require routine fixes or small refactors to update memory.
- The Skill handles both v2 project memory and v1 feature/domain documents without forcing a fixed final-answer template.

- AC-001: agent 入口文件明确说明 before/after code 文档流程。
- AC-002: managed block 外的用户规则不应被初始化覆盖。
- AC-003: agent 入口文件明确说明按需更新文档，而不是每次改动更新所有 feature docs。
- AC-004: Skill 按 none/project/guardrails/verification 分类实际 diff，判断阈值是未来 Codex 缺少该事实是否可能做出错误修改。
- AC-005: 临时执行记录、聊天过程、普通测试结果和实现流水不得写入长期项目记忆。
- AC-006: 正常最终回答不强制 NOC 固定模板；仅在记忆更新时追加一句简短说明。
- AC-007: 现行协议文档以 v2 simplified、`noc work --json` 和 memory impact 为主，不再使用旧工作流模式指导当前用户或 agent。

## Non-Goals

- 不把 NOC 协议分散到 `docs/`。


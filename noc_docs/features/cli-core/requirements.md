---
status: active
last_reviewed: 2026-07-08
source_of_truth: product-intent
confidence: medium
---

# Requirements: cli-core

## Summary

CLI 应该让人和编程助手都能用最少步骤完成 NOC 的日常工作：初始化项目、定位相关文档、维护 feature 映射、检查代码和文档是否脱节，并在需要时输出稳定的机器可读计划。

## Business Rules

- BR-001: 默认输出保持适合人阅读，避免破坏已有命令行体验。
- BR-002: 面向 agent 或自动化的输出必须是稳定 JSON，避免让工具解析自由文本。
- BR-003: `work` 命令必须能按 feature 或 path 定位相关文档，并在无法定位时给出明确 fallback。
- BR-004: `setup` 必须以幂等、非破坏方式安装或检查与 CLI 同版本的 Codex Skill，并拒绝覆盖用户自行维护的同名 Skill。

## Acceptance Criteria

- `noc work --json` returns `protocol_version` and `layout`; v2 without a precise area returns the three project-level memory files.
- `noc check` does not require a documentation edit for ordinary v2 code changes.

- AC-001: `noc work <project> --path <code/path> --json` 输出合法 JSON。
- AC-002: JSON work plan 包含 intent、paths、features、read_before_code、before_coding、update_after_code 和 finish_commands。
- AC-003: 不传 `--json` 时，原有文本 work plan 继续可用。
- AC-004: JSON work plan 包含 `schema_version`、`resolution_status`、匹配原因和低置信度下一步建议。
- AC-005: `noc work --changed --json` 和 `noc work --staged --json` 可以直接从 Git diff 路由到相关 feature。
- AC-006: `noc setup`、`noc setup --check`、`noc setup --repair` 和 `noc setup --json` 覆盖安装、只读检查、受管修复和机器可读输出。
- AC-007: `noc check --memory-impact` 接受可重复的 none/project/guardrails/verification 声明；CLI 不推断业务语义。
- AC-008: memory-impact JSON 稳定包含 memory_impact、required_docs、updated_docs 和 status。
- AC-009: `none` 不要求文档变化；长期影响必须更新对应记忆，并拒绝声明范围外的长期记忆 churn。
- AC-010: `noc --version` 输出与正式包版本一致，且不影响现有子命令。
- AC-011: 顶层帮助优先展示 `setup`、`init`、`--version` 和初始化后正常使用 Codex 的指引；其余命令保留为高级入口。

## Non-Goals

- CLI 不调用模型，也不自动改写业务代码。
- `work --json` 不负责执行文档更新，只负责给出计划。

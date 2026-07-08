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

## Acceptance Criteria

- AC-001: `noc work <project> --path <code/path> --json` 输出合法 JSON。
- AC-002: JSON work plan 包含 intent、paths、features、read_before_code、before_coding、update_after_code 和 finish_commands。
- AC-003: 不传 `--json` 时，原有文本 work plan 继续可用。
- AC-004: JSON work plan 包含 `schema_version`、`resolution_status`、匹配原因和低置信度下一步建议。
- AC-005: `noc work --changed --json` 和 `noc work --staged --json` 可以直接从 Git diff 路由到相关 feature。

## Non-Goals

- CLI 不调用模型，也不自动改写业务代码。
- `work --json` 不负责执行文档更新，只负责给出计划。

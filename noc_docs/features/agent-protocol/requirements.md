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

## Acceptance Criteria

- AC-001: agent 入口文件明确说明 before/after code 文档流程。
- AC-002: managed block 外的用户规则不应被初始化覆盖。

## Non-Goals

- 不把 NOC 协议分散到 `docs/`。


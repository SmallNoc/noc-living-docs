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

- AC-001: agent 入口文件明确说明 before/after code 文档流程。
- AC-002: managed block 外的用户规则不应被初始化覆盖。
- AC-003: agent 入口文件明确说明按需更新文档，而不是每次改动更新所有 feature docs。

## Non-Goals

- 不把 NOC 协议分散到 `docs/`。


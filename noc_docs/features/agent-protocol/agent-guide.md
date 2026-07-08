---
status: active
last_reviewed: 2026-07-08
source_of_truth: docs
confidence: medium
---

# Agent Guide: agent-protocol

## Related Documents

- Requirements: ./requirements.md
- Current status: ./status.md
- Guardrails: ./guardrails.md
- Test record: ./test-record.md
- Change record: ./change-record.md
- Notes: ./notes.md

## Read First

Read `guardrails.md` before editing this feature. Read `requirements.md` and `status.md` when behavior or intended behavior may change.

## Current Summary

这一组文件定义 agent 如何读取和维护 NOC 文档。`templates/AGENTS.md` 是通用入口的 canonical managed block，`CLAUDE.md` 和 `GEMINI.md` 指向同一协议，`protocol/` 记录更细的规则。

## Update Docs When

- Update `status.md` if behavior, API, configuration, entry points, error handling, or user flow changes.
- Update `requirements.md` if intended behavior, business rules, or acceptance criteria change.
- Append `change-record.md` for important changes.
- Append `test-record.md` after verification.


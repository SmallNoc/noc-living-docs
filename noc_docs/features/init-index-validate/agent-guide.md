---
status: active
last_reviewed: 2026-07-08
source_of_truth: docs
confidence: medium
---

# Agent Guide: init-index-validate

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

这一组脚本负责把 NOC 接入目标项目、生成 `.living-docs` 索引、校验协议结构。改动时重点保护已有项目内容不被覆盖，并确保 `init -> index -> validate -> doctor` 的基本链路仍然可跑。

## Update Docs When

- Update `status.md` if behavior, API, configuration, entry points, error handling, or user flow changes.
- Update `requirements.md` if intended behavior, business rules, or acceptance criteria change.
- Append `change-record.md` for important changes.
- Append `test-record.md` after verification.


---
status: active
last_reviewed: 2026-07-08
source_of_truth: docs
confidence: medium
---

# Agent Guide: release-quality

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

这一组文件保证 NOC 作为可发布工具保持稳定：unittest 覆盖 CLI 行为，release 脚本检查版本和 changelog，CI 运行验证。改 CLI、模板或协议时应同步测试。

## Update Docs When

- Update `status.md` if behavior, API, configuration, entry points, error handling, or user flow changes.
- Update `requirements.md` if intended behavior, business rules, or acceptance criteria change.
- Append `change-record.md` for important changes.
- Append `test-record.md` after verification.


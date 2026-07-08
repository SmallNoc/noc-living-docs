---
status: active
last_reviewed: 2026-07-08
source_of_truth: docs
confidence: medium
---

# Agent Guide: cli-core

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

`scripts/noc.py` 是统一 CLI 入口，负责把 init、index、validate、doctor、hook、check、suggest-map、work 和 feature lifecycle 命令串起来。改动 CLI 行为前先确认现有 unittest 覆盖，并优先保持已有文本输出兼容；给 agent 或自动化增加输出时，优先添加结构化选项而不是改变默认人类可读输出。

## Update Docs When

- Update `status.md` if behavior, API, configuration, entry points, error handling, or user flow changes.
- Update `requirements.md` if intended behavior, business rules, or acceptance criteria change.
- Append `change-record.md` for important changes.
- Append `test-record.md` after verification.

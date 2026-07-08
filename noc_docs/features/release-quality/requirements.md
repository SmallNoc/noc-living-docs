---
status: active
last_reviewed: 2026-07-08
source_of_truth: product-intent
confidence: medium
---

# Requirements: release-quality

## Summary

发布质量要求所有 CLI 行为、模板协议和 release bookkeeping 都有可重复验证方式。

## Business Rules

- BR-001: 新 CLI 行为必须有 unittest。
- BR-002: release 前必须通过 validate、release check、unittest 和 py_compile。

## Acceptance Criteria

- AC-001: `python -m unittest tests.test_noc_cli tests.test_release_cli` 通过。
- AC-002: `python scripts/release.py --check` 通过。

## Non-Goals

- 不在 release-quality 中实现业务功能。


---
status: active
last_reviewed: 2026-07-08
source_of_truth: tests
confidence: medium
---

# Test Record: release-quality

## Test Strategy

使用 unittest 覆盖 CLI 和 release helper，发布前再运行 py_compile、validate、release check 和 NOC 自检。

## Required Checks

- TC-001: `python -m unittest tests.test_noc_cli tests.test_release_cli`
- TC-002: `python scripts/noc.py validate`
- TC-003: `python scripts/release.py --check`

## Latest Runs

| Date | Change | Command / Method | Result | Notes |
|---|---|---|---|---|
| 2026-07-08 | baseline before agent-usability work | `python -m unittest tests.test_noc_cli tests.test_release_cli` | PASS | 47 tests passed before implementation. |


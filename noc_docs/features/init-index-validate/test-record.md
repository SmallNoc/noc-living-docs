---
status: active
last_reviewed: 2026-07-08
source_of_truth: tests
confidence: medium
---

# Test Record: init-index-validate

## Test Strategy

通过 unittest 的临时目录迁移场景验证 init/index/validate，不依赖外部项目。真实项目迁移结果记录在 `docs/migration-reports/`。

## Required Checks

- TC-001: `python -m unittest tests.test_noc_cli`
- TC-002: `python scripts/noc.py validate`

## Latest Runs

| Date | Change | Command / Method | Result | Notes |
|---|---|---|---|---|
| 2026-07-08 | initialize main repo docs | `python scripts/noc.py init . --mode small` | PASS | 生成 `AGENTS.md` 和 `noc_docs/`，随后创建真实 features。 |
| 2026-07-09 | validate standard Codex skill path | `python scripts/noc.py validate` | PASS | 仓库自检验证 `.agents/skills/project-living-docs/` 和兼容路径存在，并接受 `Use for` skill description。 |


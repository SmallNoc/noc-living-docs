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
| 2026-07-16 | feature-archive stage 2 init/index | `python -m unittest tests.test_feature_archive_init -v`; `python -m unittest tests.test_simplified_memory -v`; `python -m unittest discover -s tests`; `python scripts/noc.py validate .`; `python scripts/release.py --check`; stage-specific init/index/idempotency/no-write/wheel scripts | PASS | 11 feature-archive init/index tests passed；12 compatibility tests passed；130 total tests passed；new init creates empty `features/` and rebuildable derived indexes. |
| 2026-07-16 | feature-archive stage 1 validation | `python -m unittest tests.test_feature_archive_stage1 -v`; `python -m unittest tests.test_simplified_memory -v`; `python -m unittest discover -s tests`; `python scripts/noc.py validate .`; `python scripts/release.py --check` | PASS | 19 stage 1 tests passed；12 simplified tests passed；119 total tests passed；repository validation and release check passed. |
| 2026-07-08 | initialize main repo docs | `python scripts/noc.py init . --mode small` | PASS | 生成 `AGENTS.md` 和 `noc_docs/`，随后创建真实 features。 |
| 2026-07-09 | validate standard Codex skill path | `python scripts/noc.py validate` | PASS | 仓库自检验证 `.agents/skills/project-living-docs/` 和兼容路径存在，并接受 `Use for` skill description。 |
| 2026-07-10 | validate PyPI release files | `python scripts/noc.py validate` | PASS | 仓库自检覆盖 `docs/release.md` 和 `.github/workflows/publish.yml`。 |
| 2026-07-14 | simplified v2 initialization and v1 compatibility | `python -m unittest discover -s tests` | PASS | 87 tests；覆盖最小结构、Python/Node/Java、幂等、缺失 Skill、中文空格路径、非 Git 和 v1 不迁移。 |
| 2026-07-14 | full pytest regression | `python -m pytest -q` | PASS | 87 passed，31 subtests passed。 |


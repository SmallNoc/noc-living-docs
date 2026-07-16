---
status: active
last_reviewed: 2026-07-08
source_of_truth: tests
confidence: medium
---

# Test Record: cli-core

## Test Strategy

CLI 行为通过 `tests/test_noc_cli.py` 的 subprocess 测试验证，重点覆盖命令参数、stdout、返回码、生成文件和 JSON 可解析性。新增行为应先写失败测试，再实现。

## Required Checks

- TC-001: `python -m unittest tests.test_noc_cli`
- TC-002: `python scripts/noc.py work . --path scripts/noc.py --json`
- TC-003: 完整发布前运行 `python -m unittest discover -s tests`

## Latest Runs

| Date | Change | Command / Method | Result | Notes |
|---|---|---|---|---|
| 2026-07-16 | feature-archive candidate routing and ensure | `python -m unittest tests.test_feature_archive_routing -v`; `python -m unittest tests.test_feature_archive_ensure -v`; `python -m unittest discover -s tests` | PASS | 14 routing tests passed；8 ensure tests passed；152 total tests passed。覆盖中文 name/aliases、路径证据、歧义、索引缺失只读 fallback、ensure 幂等和旧 layout 拒绝。 |
| 2026-07-16 | feature-archive project-memory routing | `python -m unittest tests.test_simplified_memory -v`; `python -m unittest discover -s tests` | PASS | feature-archive default init now passes v2 `work/check` regressions；130 total tests passed. |
| 2026-07-16 | feature-archive stage 1 CLI recognition | `python -m unittest discover -s tests`; `python scripts/noc.py validate .`; `python scripts/release.py --check`; explicit simplified no-write hash comparison script | PASS | 119 tests passed；`validate .` passed；release check passed for 1.2.1；旧 simplified fixture 在 `work/index/doctor/validate` 后文件树和 SHA-256 未变化。 |
| 2026-07-14 | prepare v1.2.1 version output | `python -m unittest discover -s tests` | PASS | 99 tests passed，包含 `noc --version` 输出 1.2.1 的回归断言。 |
| 2026-07-14 | final CLI entry experience | `python -m unittest discover -s tests`; `python -m pytest -q` | PASS | 95 tests passed；pytest 另含 31 subtests，覆盖 `noc --version`、帮助排序及全部既有命令回归。 |
| 2026-07-14 | Skill semantic eval | `python -m unittest tests.test_noc_cli.NocCliTests.test_skill_defines_semantic_memory_impact_without_fixed_final_template -v` | PASS | 语义影响规则保留，固定最终回答模板未恢复。 |
| 2026-07-14 | semantic memory impact check | `python -m unittest discover -s tests` | PASS | 92 tests；覆盖 none、缺失对应记忆、多影响、范围外 churn、稳定 JSON 和 v1/v2 回归。 |
| 2026-07-14 | semantic memory impact check | `python -m pytest -q` | PASS | 92 passed，31 subtests passed。 |
| 2026-07-14 | v2 work/check routing and v1 command regression | `python -m unittest discover -s tests` | PASS | 87 tests；v2 返回最小项目记忆，普通代码修改不强制文档变化，v1 work/index/check/feature 保持通过。 |
| 2026-07-14 | full pytest regression | `python -m pytest -q` | PASS | 87 passed，31 subtests passed。 |
| 2026-07-08 | add `work --json` | `python -m unittest tests.test_noc_cli.NocCliTests.test_work_json_outputs_machine_readable_plan` | PASS | 验证 JSON work plan 可解析且包含关键字段。 |
| 2026-07-08 | preserve text work output | `python -m unittest tests.test_noc_cli.NocCliTests.test_work_outputs_docs_plan_for_named_feature tests.test_noc_cli.NocCliTests.test_work_resolves_feature_from_path_mapping tests.test_noc_cli.NocCliTests.test_work_does_not_modify_files` | PASS | 验证旧文本输出和只读行为仍可用。 |
| 2026-07-08 | stable JSON contract | `python -m unittest tests.test_noc_cli.NocCliTests.test_work_json_includes_stable_contract_fields` | PASS | 验证 schema、resolution status 和 path match metadata。 |
| 2026-07-08 | explicit low-confidence routing | `python -m unittest tests.test_noc_cli.NocCliTests.test_work_json_marks_missing_explicit_feature tests.test_noc_cli.NocCliTests.test_work_json_marks_unresolved_path` | PASS | 验证 missing feature/unresolved path 和 next actions。 |
| 2026-07-08 | Git-derived work paths | `python -m unittest tests.test_noc_cli.NocCliTests.test_work_json_collects_staged_paths tests.test_noc_cli.NocCliTests.test_work_json_collects_changed_paths` | PASS | 验证 `--staged` 和 `--changed` 路由。 |
| 2026-07-13 | add `noc setup` lifecycle | `python -m unittest tests.test_noc_cli tests.test_release_cli tests.test_setup_cli` | PASS | 78 tests passed, including setup install/check/repair/version/collision behavior. |

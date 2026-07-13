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
- TC-003: 完整发布前运行 `python -m unittest tests.test_noc_cli tests.test_release_cli`

## Latest Runs

| Date | Change | Command / Method | Result | Notes |
|---|---|---|---|---|
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

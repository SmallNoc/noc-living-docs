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
| 2026-07-08 | add `work --json` | `python -m unittest tests.test_noc_cli.NocCliTests.test_work_json_outputs_machine_readable_plan` | PASS | 验证 JSON work plan 可解析且包含关键字段。 |
| 2026-07-08 | preserve text work output | `python -m unittest tests.test_noc_cli.NocCliTests.test_work_outputs_docs_plan_for_named_feature tests.test_noc_cli.NocCliTests.test_work_resolves_feature_from_path_mapping tests.test_noc_cli.NocCliTests.test_work_does_not_modify_files` | PASS | 验证旧文本输出和只读行为仍可用。 |

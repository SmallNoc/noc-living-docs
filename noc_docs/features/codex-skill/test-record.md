---
status: active
last_reviewed: 2026-07-08
source_of_truth: tests
confidence: medium
---

# Test Record: codex-skill

## Test Strategy

通过文件存在性、frontmatter 和关键提示文本测试保障 Codex skill 不丢失触发说明与 JSON work plan 指引。

## Required Checks

- TC-001: `python -m unittest tests.test_noc_cli.NocCliTests.test_codex_skill_frontmatter_contains_name_and_description`
- TC-002: `python -m unittest tests.test_noc_cli.NocCliTests.test_codex_skill_references_and_evals_exist`
- TC-003: `python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json`

## Latest Runs

| Date | Change | Command / Method | Result | Notes |
|---|---|---|---|---|
| 2026-07-08 | prefer `work --json` in Codex skill | `python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json` | PASS | 验证 skill 包含 `--json` 和 machine-readable 指引。 |
| 2026-07-09 | standard Codex skill path | `python -m unittest tests.test_noc_cli.NocCliTests.test_codex_skill_frontmatter_contains_name_and_description tests.test_noc_cli.NocCliTests.test_codex_skill_references_and_evals_exist tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json` | PASS | 验证 `.agents/skills/project-living-docs` 和兼容路径都包含 skill frontmatter、references、evals，并保留 JSON work plan 指引。 |


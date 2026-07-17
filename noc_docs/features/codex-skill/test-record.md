---
status: active
last_reviewed: 2026-07-17
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
- TC-004: `python -m unittest tests.test_noc_cli.NocCliTests.test_skill_defines_feature_archive_zero_learning_workflow`
- TC-005: `python -m unittest tests.test_setup_cli.SetupCliTests.test_setup_installs_skill_into_fresh_codex_home`

## Latest Runs

| Date | Change | Command / Method | Result | Notes |
|---|---|---|---|---|
| 2026-07-17 | package both formal Skill assets | `python -m unittest discover -s tests -v`; stage 8 isolated wheel verification | PASS | 185 tests passed；wheel contained both `noc_assets/project_living_docs` and `noc_assets/codex_project_living_docs` runtime files while setup/check stayed `ready`. |
| 2026-07-17 | feature-archive zero-learning Skill workflow | `python -m unittest tests.test_noc_cli tests.test_setup_cli -v` | PASS | 80 tests passed；覆盖双 Skill 同步、完整 feature-archive 工作流、安全限制、中文规则、真实验证后才能 passed、旧布局不静默迁移、setup 安装一致性和自定义 Skill 不覆盖。 |
| 2026-07-14 | separate v2 and v1 Definition of Done | `python -m unittest discover -s tests` | PASS | 98 tests passed；v2 文档限制与两份 Skill runtime 同步均有回归覆盖。 |
| 2026-07-14 | align runtime workflow references | targeted obsolete-mode and runtime-sync unittests | PASS | 两份 reference 同步，现行协议入口不再使用旧模式。 |
| 2026-07-08 | prefer `work --json` in Codex skill | `python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json` | PASS | 验证 skill 包含 `--json` 和 machine-readable 指引。 |
| 2026-07-13 | bundle installed-command Skill | `python -m unittest tests.test_setup_cli` | PASS | 21 tests passed; formal Skill/runtime references use `noc`, both Skill trees match, and wheel contains the managed Skill manifest and references. |
| 2026-07-09 | standard Codex skill path | `python -m unittest tests.test_noc_cli.NocCliTests.test_codex_skill_frontmatter_contains_name_and_description tests.test_noc_cli.NocCliTests.test_codex_skill_references_and_evals_exist tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json` | PASS | 验证 `.agents/skills/project-living-docs` 和兼容路径都包含 skill frontmatter、references、evals，并保留 JSON work plan 指引。 |


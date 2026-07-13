---
status: active
last_reviewed: 2026-07-08
source_of_truth: tests
confidence: medium
---

# Test Record: agent-protocol

## Test Strategy

通过 unittest 检查 agent entry 模板和 Codex skill 是否包含关键协议文字。初始化和 managed block 保留行为由迁移测试覆盖。

## Required Checks

- TC-001: `python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json`
- TC-002: `python -m unittest tests.test_noc_cli`

## Latest Runs

| Date | Change | Command / Method | Result | Notes |
|---|---|---|---|---|
| 2026-07-14 | remove obsolete current workflow modes | `python -m unittest tests.test_noc_cli.NocCliTests.test_current_protocol_docs_do_not_use_obsolete_workflow_modes tests.test_setup_cli.SetupCliTests.test_standard_and_legacy_skill_runtime_content_stays_in_sync` | PASS | 现行协议入口不再包含旧模式，双 Skill runtime 保持同步。 |
| 2026-07-08 | prefer `work --json` in agent entry | `python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json` | PASS | 验证模板和 skill 明确提示 JSON work plan。 |
| 2026-07-08 | route-first protocol wording | `python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json` | PASS | 验证 README 包含 agent memory router 定位，模板和 skill 继续优先 JSON work plan。 |
| 2026-07-13 | installed CLI entry wording | `python -m unittest tests.test_setup_cli.SetupCliTests.test_formal_skill_and_user_entry_use_installed_noc_command` | PASS | 正式 Skill、workflow reference 和 AGENTS 模板不包含 `python scripts/noc.py`。 |
| 2026-07-14 | simplified Skill and managed block | `python -m unittest discover -s tests` | PASS | 87 tests；验证双 Skill 内容一致、用户 AGENTS 内容保留和 v2 managed block 幂等。 |
| 2026-07-14 | semantic memory impact Skill eval | `python -m unittest tests.test_noc_cli.NocCliTests.test_skill_defines_semantic_memory_impact_without_fixed_final_template` | PASS | 覆盖 none/project/guardrails/verification、多影响、双 Skill 一致性和简化最终回答。 |
| 2026-07-14 | full semantic memory regression | `python -m pytest -q` | PASS | 92 passed，31 subtests passed。 |


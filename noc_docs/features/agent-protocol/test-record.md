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
| 2026-07-08 | prefer `work --json` in agent entry | `python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json` | PASS | 验证模板和 skill 明确提示 JSON work plan。 |


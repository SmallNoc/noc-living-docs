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
| 2026-07-08 | tighten agent memory routing | `python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py` | PASS | Python compile check passed. |
| 2026-07-08 | tighten agent memory routing | `python -m unittest tests.test_noc_cli` | PASS | 48 CLI tests passed. |
| 2026-07-08 | tighten agent memory routing | `python -m unittest tests.test_release_cli` | PASS | 6 release tests passed. |
| 2026-07-08 | tighten agent memory routing | `python scripts/noc.py validate` | PASS | NOC Living Docs validation passed. |
| 2026-07-08 | tighten agent memory routing | `python scripts/release.py --check` | PASS | Release check passed for 1.0.0. |
| 2026-07-08 | tighten agent memory routing | `python scripts/noc.py check . --staged --warn-only` | PASS | No staged code changes requiring NOC docs check at verification time. |
| 2026-07-08 | strengthen README product entry | `python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json` | PASS | README still contains agent memory router framing. |
| 2026-07-08 | strengthen README product entry | `python -m unittest tests.test_noc_cli tests.test_release_cli` | PASS | 54 tests passed after README expansion. |
| 2026-07-08 | strengthen README product entry | `python scripts/noc.py validate` | PASS | NOC Living Docs validation passed. |
| 2026-07-08 | prepare 1.0.1 release | `python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py` | PASS | Python compile check passed. |
| 2026-07-08 | prepare 1.0.1 release | `python -m unittest tests.test_noc_cli tests.test_release_cli` | PASS | 54 tests passed. |
| 2026-07-08 | prepare 1.0.1 release | `python scripts/noc.py validate` | PASS | NOC Living Docs validation passed. |
| 2026-07-08 | prepare 1.0.1 release | `python scripts/release.py --check` | PASS | Release check passed for 1.0.1. |
| 2026-07-08 | expand bilingual README usage guide | `python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json` | PASS | README still contains agent memory router framing. |
| 2026-07-08 | expand bilingual README usage guide | `python -m unittest tests.test_noc_cli tests.test_release_cli` | PASS | 54 tests passed. |
| 2026-07-08 | expand bilingual README usage guide | `python scripts/noc.py validate` | PASS | NOC Living Docs validation passed. |
| 2026-07-08 | expand bilingual README usage guide | `python scripts/release.py --check` | PASS | Release check passed for 1.0.1. |


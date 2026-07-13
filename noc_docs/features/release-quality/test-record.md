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
| 2026-07-09 | standardize skill install and version metadata | `python -m unittest tests.test_noc_cli tests.test_release_cli` | PASS | 54 tests passed after README, skill path, test, and version metadata updates. |
| 2026-07-09 | standardize skill install and version metadata | `python scripts/noc.py validate` | PASS | NOC Living Docs validation passed after standard skill path and validation rule updates. |
| 2026-07-09 | standardize skill install and version metadata | `python scripts/release.py --check` | PASS | Release check passed with `VERSION`, `CHANGELOG.md`, README, and `pyproject.toml` aligned at 1.0.1. |
| 2026-07-09 | standardize skill install and version metadata | `python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py` | PASS | Compile check passed after validation script update. |
| 2026-07-09 | standardize skill install and version metadata | `python scripts/noc.py check . --staged --warn-only` | PASS | No staged code changes requiring NOC docs check. |
| 2026-07-10 | add PyPI publishing readiness | `python -m pip install --upgrade pip build twine pytest` | PASS | Installed local release verification tools. |
| 2026-07-10 | add PyPI publishing readiness | `python -m build` | PASS | Generated `noc_living_docs-1.0.1-py3-none-any.whl` and `noc_living_docs-1.0.1.tar.gz`; wheel contains `.living-docs` JSON and no pycache files. |
| 2026-07-10 | add PyPI publishing readiness | `python -m twine check dist/*` | PASS | Wheel and sdist passed metadata and README rendering checks. |
| 2026-07-10 | add PyPI publishing readiness | `pytest` | PASS | 57 tests passed. |
| 2026-07-10 | add PyPI publishing readiness | `python -m unittest tests.test_noc_cli tests.test_release_cli` | PASS | 57 tests passed. |
| 2026-07-10 | add PyPI publishing readiness | `python scripts/release.py --check` | PASS | Release check passed for 1.0.1 and now verifies pyproject/README version consistency. |
| 2026-07-10 | add PyPI publishing readiness | `python -m pip install --force-reinstall dist/noc_living_docs-1.0.1-py3-none-any.whl; noc --help; noc init <temp>` | PASS | Installed wheel exposes `noc` entry point and initializes `noc_docs/.living-docs/config.json`. |
| 2026-07-10 | add PyPI publishing readiness | `PyYAML safe_load on .github/workflows/*.yml` | PASS | `publish.yml`, `validate.yml`, and `noc-check.yml` parsed successfully. |
| 2026-07-10 | bump release target to 1.0.2 | `python scripts/release.py --check` | PASS | Release check passed for 1.0.2 after avoiding the existing `v1.0.1` tag. |
| 2026-07-10 | bump release target to 1.0.2 | `python -m unittest tests.test_noc_cli tests.test_release_cli` | PASS | 57 tests passed. |
| 2026-07-10 | bump release target to 1.0.2 | `pytest` | PASS | 57 tests passed. |
| 2026-07-10 | bump release target to 1.0.2 | `python -m build` | PASS | Generated `noc_living_docs-1.0.2-py3-none-any.whl` and `noc_living_docs-1.0.2.tar.gz`. |
| 2026-07-10 | bump release target to 1.0.2 | `python -m twine check dist/*` | PASS | 1.0.2 wheel and sdist passed metadata and README rendering checks. |
| 2026-07-10 | bump release target to 1.0.2 | `python -m pip install --force-reinstall dist/noc_living_docs-1.0.2-py3-none-any.whl; noc --help; noc init <temp>` | PASS | Installed 1.0.2 wheel exposes `noc` entry point and initializes `noc_docs/.living-docs/config.json`. |
| 2026-07-10 | bump release target to 1.0.2 | `python scripts/noc.py validate` | PASS | NOC Living Docs validation passed. |
| 2026-07-10 | bump release target to 1.0.2 | `python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py` | PASS | Compile check passed. |
| 2026-07-10 | isolate release tests from tag env | `GITHUB_REF_TYPE=tag GITHUB_REF_NAME=v1.0.2 python -m pytest` | PASS | 57 tests passed with simulated GitHub tag environment. |
| 2026-07-10 | isolate release tests from tag env | `GITHUB_REF_TYPE=tag GITHUB_REF_NAME=v1.0.2 python -m unittest tests.test_noc_cli tests.test_release_cli` | PASS | 57 tests passed with simulated GitHub tag environment. |
| 2026-07-10 | isolate release tests from tag env | `GITHUB_REF_TYPE=tag GITHUB_REF_NAME=v1.0.2 python scripts/release.py --check` | PASS | Repository release check passed for 1.0.2 under tag environment. |
| 2026-07-10 | isolate release tests from tag env | `python -m build` | PASS | Generated `noc_living_docs-1.0.2-py3-none-any.whl` and `noc_living_docs-1.0.2.tar.gz`. |
| 2026-07-10 | isolate release tests from tag env | `python -m twine check dist/*` | PASS | 1.0.2 wheel and sdist passed metadata and README rendering checks. |
| 2026-07-10 | make staged-check tests independent of global Git identity | `GIT_CONFIG_GLOBAL=<missing> GITHUB_REF_TYPE=tag GITHUB_REF_NAME=v1.0.2 python -m pytest` | PASS | 57 tests passed under the same missing-global-Git-identity and tag-event conditions as the failing publish workflow. |
| 2026-07-10 | make staged-check tests independent of global Git identity | `GIT_CONFIG_GLOBAL=<missing> GITHUB_REF_TYPE=tag GITHUB_REF_NAME=v1.0.2 python -m unittest tests.test_noc_cli tests.test_release_cli` | PASS | 57 tests passed. |
| 2026-07-10 | make staged-check tests independent of global Git identity | `GITHUB_REF_TYPE=tag GITHUB_REF_NAME=v1.0.2 python scripts/release.py --check` | PASS | Release check passed for 1.0.2. |
| 2026-07-10 | make staged-check tests independent of global Git identity | `python scripts/noc.py validate` | PASS | NOC Living Docs validation passed. |
| 2026-07-10 | make staged-check tests independent of global Git identity | `python -m build` | PASS | Generated `noc_living_docs-1.0.2-py3-none-any.whl` and `noc_living_docs-1.0.2.tar.gz`. |
| 2026-07-10 | make staged-check tests independent of global Git identity | `python -m twine check dist/*` | PASS | 1.0.2 wheel and sdist passed metadata and README rendering checks. |
| 2026-07-13 | setup installation closure | `python -m unittest tests.test_noc_cli tests.test_release_cli tests.test_setup_cli` | PASS | 78 tests passed. |
| 2026-07-13 | setup installation closure | `python -m pytest` | PASS | 78 tests passed. |
| 2026-07-13 | setup installation closure | `python scripts/noc.py validate`; `python scripts/release.py --check`; `python -m py_compile ...` | PASS | Protocol, release metadata, and compilation checks passed for 1.0.2. |
| 2026-07-13 | wheel-installed setup | Build wheel, install into isolated venv outside the repository, run setup/check/damaged default/repair JSON flows with a Unicode and space-containing `CODEX_HOME` | PASS | Exit codes were 0/0/1/0; JSON stayed parseable and wheel resources were used without source checkout paths. |
| 2026-07-13 | prepare 1.1.0 installation release | `python -m unittest tests.test_noc_cli tests.test_release_cli tests.test_setup_cli`; `python -m pytest` | PASS | Both complete runners passed all 80 tests, including version preparation on a previous release tag and Skill manifest version mismatch detection. |
| 2026-07-13 | prepare 1.1.0 installation release | `python scripts/noc.py validate`; `python scripts/release.py --check`; `git diff --check` | PASS | Living docs validation and release metadata checks passed for 1.1.0; diff check reported only line-ending conversion warnings. |
| 2026-07-13 | isolated 1.1.0 wheel verification | Build `noc_living_docs-1.1.0-py3-none-any.whl`, install outside the repository, then run `noc --help`, `noc setup --json`, `noc setup --check --json`, and `noc setup --repair --json` with a Unicode and space-containing `CODEX_HOME` | PASS | Wheel METADATA, installed CLI, bundled manifest, and all setup JSON responses reported 1.1.0; the wheel contained the Skill, references, and eval CSV. |
| 2026-07-13 | remote setup test gate | Inspect `.github/workflows/validate.yml` and `.github/workflows/publish.yml` | PASS | Both workflows now run `tests.test_setup_cli` with the existing CLI and release suites. |
| 2026-07-13 | GitHub Actions PR validation run 11 | `Validate` | FAIL | The setup wheel test reached `python -m build`, but the PR runner had not installed the `build` test dependency; product checks before that step passed. The workflow now installs `build` and keeps the test enabled. |


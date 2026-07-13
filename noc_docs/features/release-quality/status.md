---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: release-quality

## Current Behavior

测试通过 Python unittest 和 pytest 运行，覆盖 CLI help、setup/init/index/check/doctor/work/feature lifecycle、Codex Skill 安装保护、release 脚本、PyPI publish workflow 和打包元数据。wheel 同时包含项目模板和带版本清单的 `project-living-docs` Skill 运行文件。当前开发版本为 `1.2.0`（Unreleased）；`1.1.0` 已发布，本分支不会创建 tag 或发布 PyPI。

PR 验证运行完整 tests discovery；tag 发布 workflow 在 wheel 安装后先执行 `noc setup`，再验证 simplified init，因此远程门禁覆盖 Skill 安装与新项目初始化闭环。

## Important Files

- `tests/test_noc_cli.py`
- `tests/test_release_cli.py`
- `scripts/release.py`
- `pyproject.toml`
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `docs/release.md`
- `.github/workflows/publish.yml`
- `.gitignore`
- `.agents/skills/project-living-docs/`
- `tests/test_setup_cli.py`

## Data, API, or Configuration

- Python package entry point: `noc = "scripts.noc:main"`
- `README.md` 是项目主要产品入口，归入 release-quality 路由。
- `pyproject.toml` package version 当前为 `1.2.0`，与 `VERSION`、README、CHANGELOG 和 Skill 清单保持一致。
- `pyproject.toml` 使用 SPDX license expression、`license-files = ["LICENSE"]`、显式 package data，确保 wheel 包含 `templates/noc_docs/.living-docs/*.json` 且不包含 `__pycache__`。
- `.github/workflows/publish.yml` 使用 `permissions.contents: read` 和 `permissions.id-token: write`，environment 为 `pypi`，不使用 token secret。
- wheel 内的 Skill package 路径为 `noc_assets/project_living_docs/`，安装目标为 `$CODEX_HOME/skills/project-living-docs/`；集成测试从仓库外工作目录启动隔离 venv，避免源码路径遮蔽 wheel。

## Known Issues

- 无专门集成测试模拟真实 Codex 会话；主要通过 CLI subprocess 和文本断言覆盖。


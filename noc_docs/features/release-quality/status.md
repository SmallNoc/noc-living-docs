---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: release-quality

## Current Behavior

测试通过 Python unittest 和 pytest 运行，覆盖 CLI help、init/index/check/doctor/work/feature lifecycle、Codex skill 文件存在性、release 脚本、PyPI publish workflow 和打包元数据。当前支持通过 `python -m build` 构建 PyPI wheel/sdist，并通过 `.github/workflows/publish.yml` 在 `v*` tag push 时使用 PyPI Trusted Publishing 发布。当前准备发布版本为 `1.0.2`。

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

## Data, API, or Configuration

- Python package entry point: `noc = "scripts.noc:main"`
- `README.md` 是项目主要产品入口，归入 release-quality 路由。
- `pyproject.toml` package version 当前为 `1.0.2`，与 `VERSION`、README 和 CHANGELOG 保持一致。
- `pyproject.toml` 使用 SPDX license expression、`license-files = ["LICENSE"]`、显式 package data，确保 wheel 包含 `templates/noc_docs/.living-docs/*.json` 且不包含 `__pycache__`。
- `.github/workflows/publish.yml` 使用 `permissions.contents: read` 和 `permissions.id-token: write`，environment 为 `pypi`，不使用 token secret。

## Known Issues

- 无专门集成测试模拟真实 Codex 会话；主要通过 CLI subprocess 和文本断言覆盖。


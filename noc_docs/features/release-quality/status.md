---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: release-quality

## Current Behavior

测试通过 Python unittest 运行，覆盖 CLI help、init/index/check/doctor/work/feature lifecycle、Codex skill 文件存在性和 release 脚本。当前新增了 `work --json`、Git diff routing、agent 入口优先 JSON、标准 `.agents/skills/project-living-docs/` skill 路径和 README 安装说明的测试。当前准备发布版本为 `1.0.1`。

## Important Files

- `tests/test_noc_cli.py`
- `tests/test_release_cli.py`
- `scripts/release.py`
- `pyproject.toml`
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `.agents/skills/project-living-docs/`

## Data, API, or Configuration

- Python package entry point: `noc = "scripts.noc:main"`
- `README.md` 是项目主要产品入口，归入 release-quality 路由。
- `pyproject.toml` package version 当前为 `1.0.1`，与 `VERSION`、README 和 CHANGELOG 保持一致。

## Known Issues

- 无专门集成测试模拟真实 Codex 会话；主要通过 CLI subprocess 和文本断言覆盖。


---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: release-quality

## Current Behavior

测试通过 Python unittest 运行，覆盖 CLI help、init/index/check/doctor/work/feature lifecycle、Codex skill 文件存在性和 release 脚本。当前新增了 `work --json` 和 agent 入口优先 JSON 的测试。

## Important Files

- `tests/test_noc_cli.py`
- `tests/test_release_cli.py`
- `scripts/release.py`
- `pyproject.toml`
- `CHANGELOG.md`
- `VERSION`

## Data, API, or Configuration

- Python package entry point: `noc = "scripts.noc:main"`

## Known Issues

- 无专门集成测试模拟真实 Codex 会话；主要通过 CLI subprocess 和文本断言覆盖。


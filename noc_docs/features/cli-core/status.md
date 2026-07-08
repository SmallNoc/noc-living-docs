---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: cli-core

## Current Behavior

`scripts/noc.py` 提供统一子命令入口。`work` 可以根据 `--feature` 或 `--path` 输出改代码前要读的文档、编码前要记录的需求或问题、改完后要更新的文档，以及收尾检查命令。当前新增 `--json` 后，agent 可以直接读取结构化 work plan；默认文本输出仍保持向后兼容。

## Important Files

- `scripts/noc.py`
- `tests/test_noc_cli.py`
- `noc_docs/.living-docs/feature-map.json`

## Data, API, or Configuration

- `noc_docs/.living-docs/feature-map.json` 负责把代码路径映射到 feature。
- `work --json` 输出 work plan JSON，不写文件。

## Known Issues

- `doctor` 和 `check` 目前仍主要输出文本；如后续需要更深自动化，可继续补 `--json`。

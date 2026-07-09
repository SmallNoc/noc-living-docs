---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: init-index-validate

## Current Behavior

`init-noc-docs.py` 负责复制模板和合并 agent managed block；`index-noc-docs.py` 生成 manifest、docs-index 和 feature-map；`validate-noc-docs.py` 校验本仓库或目标项目的协议结构。仓库自检同时要求标准 `.agents/skills/project-living-docs/`、兼容 `skills/codex/project-living-docs/`、release 文档和 PyPI publish workflow 存在，并允许 skill description 使用 `Use when` 或 `Use for` 开头。

## Important Files

- `scripts/init-noc-docs.py`
- `scripts/index-noc-docs.py`
- `scripts/validate-noc-docs.py`
- `.agents/skills/project-living-docs/`
- `skills/codex/project-living-docs/`

## Data, API, or Configuration

- `noc_docs/.living-docs/config.json`
- `noc_docs/.living-docs/feature-map.json`

## Known Issues

- `suggest-map` 对平铺 CLI 仓库可能返回空数组，这是允许的。


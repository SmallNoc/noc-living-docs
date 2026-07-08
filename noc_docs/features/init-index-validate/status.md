---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: init-index-validate

## Current Behavior

`init-noc-docs.py` 负责复制模板和合并 agent managed block；`index-noc-docs.py` 生成 manifest、docs-index 和 feature-map；`validate-noc-docs.py` 校验本仓库或目标项目的协议结构。

## Important Files

- `scripts/init-noc-docs.py`
- `scripts/index-noc-docs.py`
- `scripts/validate-noc-docs.py`

## Data, API, or Configuration

- `noc_docs/.living-docs/config.json`
- `noc_docs/.living-docs/feature-map.json`

## Known Issues

- `suggest-map` 对平铺 CLI 仓库可能返回空数组，这是允许的。


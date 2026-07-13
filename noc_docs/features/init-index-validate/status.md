---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: init-index-validate

## Current Behavior

`noc init` 对未指定 `--mode` 的新项目生成 protocol v2 简化结构：三个项目级 Markdown 和记忆配置、路由、清单；它从 README、项目标志、源码和测试目录提取可确认事实，并保留已有 AGENTS 内容。显式 small/domain/auto 和已有 features/domains 项目仍走 v1 流程。`index`、`validate` 和 `doctor` 可识别两种协议，本仓库自身保持 v1。

## Important Files

- `scripts/init-noc-docs.py`
- `scripts/index-noc-docs.py`
- `scripts/validate-noc-docs.py`
- `.agents/skills/project-living-docs/`
- `skills/codex/project-living-docs/`

## Data, API, or Configuration

- `noc_docs/.living-docs/config.json`
- `noc_docs/.living-docs/feature-map.json`
- v2: `config.json`、`routing.json`、`manifest.json`

## Known Issues

- `suggest-map` 对平铺 CLI 仓库可能返回空数组，这是允许的。


---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Project Status

## Summary

NOC Living Docs 是一个 Python CLI 和文档协议，用固定的 `noc_docs/` 结构帮助人和 AI agent 在改代码前读对文档、改完后同步需求/现状/测试/变更记录。

## Tech Stack

- Python 3.10+
- argparse CLI
- Markdown templates
- JSON indexes under `noc_docs/.living-docs/`
- unittest test suite

## Current Capabilities

- 初始化 small/domain 模式的 NOC 文档结构。
- 生成 docs index、manifest 和 feature-map。
- 根据代码路径或 feature 输出 work plan。
- 检查 staged code changes 是否有对应 NOC docs updates。
- 为 Codex 和通用 agents 提供入口协议。

## Important Entry Points

- `scripts/noc.py`
- `templates/AGENTS.md`
- `skills/codex/project-living-docs/SKILL.md`
- `noc_docs/docs-map.md`

## Known Risks

- `doctor` 和 `check` 仍以文本输出为主，自动化消费能力弱于 `work --json`。
- 平铺 CLI 仓库的 `suggest-map` 可能返回空数组，这是允许结果，但需要用户理解。

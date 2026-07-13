---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: cli-core

## Current Behavior

Bare `noc init` now establishes simplified v2 project memory after verifying the installed Skill. Existing v1 layouts and explicit `--mode` invocations retain the legacy command and document behavior. `work` routes v2 to the three project-level files, while `check` treats v2 documentation updates as semantic rather than mandatory.

`noc check` 现在接受可重复的 `--memory-impact` 和可选 `--json`。声明 `none` 时无需更新项目记忆；project、guardrails、verification 分别校验 v2 的三个既有文件。JSON 只输出稳定的四字段，默认未传新参数的 v1/v2 check 行为保持兼容。

`scripts/noc.py` 提供统一子命令入口。`setup` 将 wheel 内置的同版本 `project-living-docs` Skill 安装到 `$CODEX_HOME/skills`，支持只读检查、受管修复和 JSON 输出。受管身份同时校验 schema、Skill 名称、管理方和稳定 manager id；目录替换使用完整临时副本、备份回滚和冲突保护。`work` 的原有文本和 JSON 行为保持兼容。

## Important Files

- `scripts/noc.py`
- `tests/test_noc_cli.py`
- `noc_docs/.living-docs/feature-map.json`

## Data, API, or Configuration

- `noc_docs/.living-docs/feature-map.json` 负责把代码路径映射到 feature。
- `work --json` 输出 work plan JSON，不写文件。
- `resolution_status` 当前取值为 `resolved`、`unresolved` 或 `missing_feature`。
- `CODEX_HOME` 可覆盖 Codex 根目录；未设置时使用 `~/.codex`。

## Known Issues

- `doctor` 和 `check` 目前仍主要输出文本；如后续需要更深自动化，可继续补 `--json`。

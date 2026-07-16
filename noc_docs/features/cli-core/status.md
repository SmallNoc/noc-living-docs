---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: cli-core

## Current Behavior

Bare `noc init` now establishes simplified v2 project memory after verifying the installed Skill. Existing v1 layouts and explicit `--mode` invocations retain the legacy command and document behavior. `work` routes v2 to the three project-level files, while `check` treats v2 documentation updates as semantic rather than mandatory.

`noc --version` 输出 `noc-living-docs 1.2.1`，版本来自既有单一版本来源。顶层帮助优先列出 `setup`、`init` 和 `--version`，并将其他保留命令标记为 Advanced。

`noc check` 现在接受可重复的 `--memory-impact` 和可选 `--json`。声明 `none` 时无需更新项目记忆；project、guardrails、verification 分别校验 v2 的三个既有文件。JSON 只输出稳定的四字段，默认未传新参数的 v1/v2 check 行为保持兼容。

`scripts/noc.py` 提供统一子命令入口。`setup` 将 wheel 内置的同版本 `project-living-docs` Skill 安装到 `$CODEX_HOME/skills`，支持只读检查、受管修复和 JSON 输出。受管身份同时校验 schema、Skill 名称、管理方和稳定 manager id；目录替换使用完整临时副本、备份回滚和冲突保护。`work` 的原有文本和 JSON 行为保持兼容。

阶段 1 feature-archive MVP 增加了只读 schema/layout 识别基础：`scripts.noclib.schemas` 校验 feature-archive config、overview frontmatter、candidate、patch 和 evidence payload 的基础形状；`scripts.noclib.layouts` 识别 simplified、feature-archive、v1 small 和 v1 domain。`doctor` 可识别 feature-archive layout，报告 `language` 与 `machine_keys` 配置，并保持只读。`validate` 现在同时支持 `noc validate <target>` 和 `noc validate --target <target>`。

## Important Files

- `scripts/noc.py`
- `tests/test_noc_cli.py`
- `noc_docs/.living-docs/feature-map.json`

## Data, API, or Configuration

- `noc_docs/.living-docs/feature-map.json` 负责把代码路径映射到 feature。
- `work --json` 输出 work plan JSON，不写文件。
- `resolution_status` 当前取值为 `resolved`、`unresolved` 或 `missing_feature`。
- `CODEX_HOME` 可覆盖 Codex 根目录；未设置时使用 `~/.codex`。
- `language` 与 `machine_keys` 是 v2 layout 的文档语言和机器字段配置；feature-archive 要求 `language: zh-CN` 合法且 `machine_keys: en-US` 保持英文机器字段。

## Known Issues

- `doctor` 和 `check` 目前仍主要输出文本；如后续需要更深自动化，可继续补 `--json`。

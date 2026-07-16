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

阶段 2 中 `work` 和 `check --memory-impact` 将 feature-archive 识别为 v2 项目记忆布局。`work --json` 对 feature-archive 返回项目级三文件和 `layout_version`。

阶段 3 为 feature-archive 项目增加候选识别和功能确保。`work --json` 读取 `feature-index.json`，在索引缺失或损坏时只读扫描 `features/*/overview.md`，基于 feature-id、中文或英文名称、aliases、overview 正文关键词、反引号代码路径、测试路径与代码范围关联和状态惩罚生成候选分数、证据和置信度；top1/top2 分数接近时返回 `action: ask_user`。`noc feature ensure <project> --id <feature-id> --name <name>` 只用于 feature-archive layout，幂等创建 `noc_docs/features/<feature-id>/overview.md`，并在创建成功后重建派生索引。

阶段 4 为 feature-archive 项目增加 `noc feature update <project> --id <feature-id> --patch-file <patch.json> --json`。CLI 只接受结构化 patch，不理解自然语言、不运行测试、不写业务代码；它局部更新 `overview.md` 的中文章节，使用 `<!-- noc:id=... -->` 稳定定位受管理条目，保留未知章节和用户手工内容。实际修改前会备份原 overview，使用原子写入，支持可选 `expected_overview_sha256` 并发保护；无变化时返回 `unchanged` 且不创建备份。

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
- feature-archive 阶段 3 的 candidate routing 输出 `candidates`、`ambiguity` 和 `action`，但 CLI 只给出证据和分数，最终语义选择仍由 Skill 或用户确认。
- `noc feature ensure` 要求稳定 ASCII kebab-case `--id`，中文显示名保存在 `name`，`--alias` 可重复，`--intent` 只写入初始“已确认需求”章节；已存在同 id 时不覆盖用户内容。
- `noc feature update` 的 patch 字段覆盖已确认需求、当前实现、重要约束、代码范围、验证方式、最近验证结果、最近重大变更和待确认事项；验证结果必须由 patch 显式提供，`passed` 必须有 `exit_code: 0`。

## Known Issues

- `doctor` 和 `check` 目前仍主要输出文本；如后续需要更深自动化，可继续补 `--json`。

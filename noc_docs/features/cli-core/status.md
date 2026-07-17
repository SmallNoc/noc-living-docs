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

阶段 5 为 feature-archive 项目增加 evidence 和 feature impact check。`noc evidence <project> --staged --json` 只读收集真实 staged Git diff，输出 changed paths、diff 统计和确定性 signals，不运行测试、不推断 passed、不修改 Markdown、索引、Git index 或工作树。`noc evidence record <project> --feature-id <feature-id> --file <json> --json` 只记录 Skill 已执行后提交的验证证据，要求 feature 存在、layout 为 feature-archive、`passed` 必须有真实 `exit_code: 0`，并对 command 和 output summary 脱敏后原子写入 evidence 文件与派生 evidence index。

`noc check <project> --feature-impact-file <impact.json> --json` 校验 Skill 提交的结构化 feature impact 声明，覆盖 `none`、`implementation`、`requirement` 和 `major`。CLI 检查功能存在、声明章节实际存在、verification evidence 与 feature 匹配、failed/not_run evidence 不会被伪装成 passed、major change id 出现在 overview 中；它只报告错误和 warning，不写 overview、不写 evidence、不运行测试、不自动分类 change_class。既有 `noc check --memory-impact ... --json` 合同保持兼容。

阶段 6 增加了显式迁移入口 `noc migrate`。`--to feature-archive --dry-run --json` 使用与 apply 相同的规划逻辑并保持零写入；`--apply --backup --json` 才会迁移旧 simplified 或 v1 small/domain 项目，并在项目根 `.noc-backups/migrations/<backup-id>/` 保存完整 `noc_docs` 备份和 SHA-256 manifest。`--rollback <backup-id> --json` 只接受当前项目内合法备份，校验 manifest 后恢复 `noc_docs`，并在恢复前再次备份当前状态。普通 `work/index/doctor/validate/check/evidence` 命令不会创建 `features/`、改写 layout 或创建迁移备份。

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
- `noc evidence` 的代码证据 schema_version 为 `1.0`，支持 staged added/modified/deleted/renamed、Windows `/` 路径规范化、中文路径和 test/api/database/config/security/documentation signals。
- `noc evidence record` 的验证证据保存到 `noc_docs/.living-docs/evidence/<feature-id>/<evidence-id>.json`；`evidence-id` 由 feature_id、command、cwd、started_at、finished_at、exit_code、result 和 scope 稳定哈希生成，相同证据重复提交返回 `existing`。
- `noc check --feature-impact-file` 的 impact schema_version 为 `1.0`，`change_class` 只允许 `none`、`implementation`、`requirement`、`major`；多功能变更使用 `documentation_updates` 按 feature 拆分。
- `noc migrate` 的 dry-run/apply JSON 包含 `source_layout`、`target_layout`、`can_apply`、`operations`、`conflicts`、`warnings` 和 `backup_scope`；apply 额外返回 `backup_id`、`backup_path`、`backup_file_count` 和 `rollback.rollback_command`。

## Known Issues

- `doctor` 和 `check` 目前仍主要输出文本；如后续需要更深自动化，可继续补 `--json`。

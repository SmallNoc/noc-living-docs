---
status: active
last_reviewed: 2026-07-17
source_of_truth: code
confidence: medium
---

# Current Status: codex-skill

## Current Behavior

`.agents/skills/project-living-docs/` 是 wheel 打包和 `noc setup` 安装的标准 Skill 源，带有 `noc-skill.json` 版本与管理清单；`skills/codex/project-living-docs/` 继续保留以兼容已有用法。正式 Skill 和运行时 references 统一调用已安装的 `noc` 命令。

Definition of Done 现按协议拆分：v2 simplified 仅根据 memory impact 维护 `project.md`、`guardrails.md`、`verification.md`；v1 legacy 保留 feature/domain 的 requirements、status、test 和 change 记录规则。

运行时 workflow reference 不再使用旧的分级模式；Codex 统一通过 `noc work --json` 路由，并根据 protocol version 与 memory impact 选择 v2 或 legacy v1 规则。

阶段 7 后，双 Skill 增加 feature-archive 零学习工作流：Codex 先用 `noc work` 识别相关功能，高置信度自动选择已有功能，明确新业务功能用 `noc feature ensure` 创建，歧义时只问用户一次；改代码前读取 `project.md`、`guardrails.md`、`verification.md` 和相关 `overview.md`，改完后运行真实验证，调用 `noc evidence`、`noc evidence record`、`noc feature update` 和 `noc check --feature-impact-file` 收口。

Skill 现在明确禁止自由重写整个 `overview.md`、未确认就写入已确认需求、未执行测试却写 passed、把计划写成当前实现、把普通修改写成重大变更、机械按源码目录创建功能，以及静默迁移 simplified/small/domain。`language: zh-CN` 项目要求功能名称、overview 正文、验证摘要和最终汇报使用简体中文，同时保留 key、feature id、CLI 参数、路径、代码标识和命令的英文或原文。

## Important Files

- `.agents/skills/project-living-docs/SKILL.md`
- `.agents/skills/project-living-docs/references/`
- `.agents/skills/project-living-docs/evals/`
- `skills/codex/project-living-docs/SKILL.md`
- `skills/codex/project-living-docs/references/`
- `skills/codex/project-living-docs/evals/`

## Data, API, or Configuration

- 标准路径和兼容路径的 skill frontmatter `name` 和 `description` 被测试覆盖。
- `noc-skill.json` 记录 Skill 名称、版本、管理方、稳定 manager id 和正式运行必需文件。
- 自动测试按规范化换行比较标准与兼容 Skill 的全部 runtime content，防止两套副本漂移。
- `noc setup` 安装的 Skill 内容与 `.agents/skills/project-living-docs/` 正式源逐文件一致；用户自定义同名 Skill 仍拒绝覆盖。
- 阶段 8 后，wheel 同时包含标准 Skill 资产 `noc_assets.project_living_docs` 和兼容 Skill 资产 `noc_assets.codex_project_living_docs`。`noc setup` 仍只安装标准 NOC-managed Skill；兼容资产用于发布包审计和继续保证两份正式 Skill runtime 内容同步。

## Known Issues

- evals 目前覆盖触发/不触发样例，但不是完整行为模拟。


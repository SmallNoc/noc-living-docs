---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: codex-skill

## Current Behavior

`.agents/skills/project-living-docs/` 是 wheel 打包和 `noc setup` 安装的标准 Skill 源，带有 `noc-skill.json` 版本与管理清单；`skills/codex/project-living-docs/` 继续保留以兼容已有用法。正式 Skill 和运行时 references 统一调用已安装的 `noc` 命令。

Definition of Done 现按协议拆分：v2 simplified 仅根据 memory impact 维护 `project.md`、`guardrails.md`、`verification.md`；v1 legacy 保留 feature/domain 的 requirements、status、test 和 change 记录规则。

运行时 workflow reference 不再使用旧的分级模式；Codex 统一通过 `noc work --json` 路由，并根据 protocol version 与 memory impact 选择 v2 或 legacy v1 规则。

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

## Known Issues

- evals 目前覆盖触发/不触发样例，但不是完整行为模拟。


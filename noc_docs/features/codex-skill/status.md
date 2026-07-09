---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: codex-skill

## Current Behavior

`.agents/skills/project-living-docs/SKILL.md` 是推荐给 Codex 扫描和复制的标准 skill 路径，`skills/codex/project-living-docs/SKILL.md` 继续保留以兼容已有用法。skill 要求 Codex 在代码可能变化时运行 work plan，并优先使用 `--json` 获取机器可读路由。reference 文件保存详细 workflow、feature doc 模板、domain mode 和推荐提示。

## Important Files

- `.agents/skills/project-living-docs/SKILL.md`
- `.agents/skills/project-living-docs/references/`
- `.agents/skills/project-living-docs/evals/`
- `skills/codex/project-living-docs/SKILL.md`
- `skills/codex/project-living-docs/references/`
- `skills/codex/project-living-docs/evals/`

## Data, API, or Configuration

- 标准路径和兼容路径的 skill frontmatter `name` 和 `description` 被测试覆盖。

## Known Issues

- evals 目前覆盖触发/不触发样例，但不是完整行为模拟。


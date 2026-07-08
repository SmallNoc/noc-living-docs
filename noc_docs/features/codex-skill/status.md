---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: codex-skill

## Current Behavior

`skills/codex/project-living-docs/SKILL.md` 当前要求 Codex 在代码可能变化时运行 work plan，并优先使用 `--json` 获取机器可读路由。reference 文件保存详细 workflow、feature doc 模板、domain mode 和推荐提示。

## Important Files

- `skills/codex/project-living-docs/SKILL.md`
- `skills/codex/project-living-docs/references/`
- `skills/codex/project-living-docs/evals/`

## Data, API, or Configuration

- skill frontmatter 的 `name` 和 `description` 被测试覆盖。

## Known Issues

- evals 目前覆盖触发/不触发样例，但不是完整行为模拟。


---
status: active
last_reviewed: 2026-07-08
source_of_truth: policy
confidence: medium
---

# Guardrails: codex-skill

## Forbidden

- G-001: 不要让 skill 绕过 NOC 文档检查流程直接改代码。
- G-002: 不要把 Codex 专用规则写成与通用 AGENTS 协议冲突。

## Requires Approval

- A-001: 改变触发范围或停止条件前需要补 eval 或测试。

## Must Preserve

- P-001: final response 需要报告 NOC docs checked/updated/unchanged。

## Sensitive Files

- `.agents/skills/project-living-docs/SKILL.md`
- `skills/codex/project-living-docs/SKILL.md`


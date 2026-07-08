---
status: active
last_reviewed: 2026-07-08
source_of_truth: policy
confidence: medium
---

# Guardrails: cli-core

## Forbidden

- G-001: 不要改变现有命令的默认文本输出语义，除非同步更新测试和 README。
- G-002: 不要让 CLI 自动调用模型。

## Requires Approval

- A-001: 默认严格度、hook 阻断策略或 destructive repair 行为发生变化前需要明确确认。

## Must Preserve

- P-001: 已有 agent entry 文件中 NOC managed block 之外的用户内容必须保留。
- P-002: JSON 输出字段应保持稳定，新增字段优先兼容旧消费者。

## Sensitive Files

- `scripts/noc.py`
- `templates/AGENTS.md`
- `skills/codex/project-living-docs/SKILL.md`

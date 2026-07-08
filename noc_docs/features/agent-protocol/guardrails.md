---
status: active
last_reviewed: 2026-07-08
source_of_truth: policy
confidence: medium
---

# Guardrails: agent-protocol

## Forbidden

- G-001: 不要让 agent 创建 `docs/` 作为 NOC 协议根。
- G-002: 不要让模板规则和 Codex skill 的流程互相冲突。

## Requires Approval

- A-001: 改变 managed block 标记或 canonical 模板前需要确认迁移影响。

## Must Preserve

- P-001: 用户在 agent 文件 managed block 外的规则必须保留。

## Sensitive Files

- `templates/AGENTS.md`
- `AGENTS.md`


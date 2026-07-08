---
status: active
last_reviewed: 2026-07-08
source_of_truth: policy
confidence: medium
---

# Guardrails: init-index-validate

## Forbidden

- G-001: 不要默认覆盖已有 `noc_docs/` 文件。
- G-002: 不要把已有非 NOC `docs/` 迁移或删除。

## Requires Approval

- A-001: 改变 auto mode 判定规则前需要补迁移测试。

## Must Preserve

- P-001: feature-map 中已有 paths 和自定义元数据必须保留。

## Sensitive Files

- `scripts/init-noc-docs.py`
- `scripts/index-noc-docs.py`
- `templates/noc_docs/`


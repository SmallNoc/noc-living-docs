---
status: active
last_reviewed: 2026-07-08
source_of_truth: policy
confidence: medium
---

# Guardrails: release-quality

## Forbidden

- G-001: 不要发布未通过 release check 的版本。
- G-002: 不要只靠手工测试验证新增 CLI 行为。
- G-003: 不要把 PyPI token、密码或 API key 写入代码、README、workflow 或 NOC 文档。

## Requires Approval

- A-001: 变更版本号、license 或发布流程前需要明确确认。

## Must Preserve

- P-001: 保持 `VERSION`、`CHANGELOG.md` 和 Git tag 语义一致。

## Sensitive Files

- `scripts/release.py`
- `VERSION`
- `CHANGELOG.md`
- `pyproject.toml`
- `.github/workflows/publish.yml`
- `docs/release.md`


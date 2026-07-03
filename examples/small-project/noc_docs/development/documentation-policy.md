# Documentation Policy

## Update Rules

Update NOC docs only when the change affects:

- behavior
- requirements
- API or CLI contracts
- configuration
- tests or verification strategy
- deployment or operations
- guardrails
- architecture or module boundaries

Pure formatting, internal cleanup, or no-behavior-change refactors do not require feature doc updates unless they affect maintainability guidance.

## Conflict Rules

如果需求、现状和代码不一致：

- 当前行为以代码为准，并更新 `status.md`。
- 产品意图不要从代码中猜测。
- 未解决的问题记录到 `notes.md`。
- 涉及 `guardrails.md` 的冲突必须询问用户。


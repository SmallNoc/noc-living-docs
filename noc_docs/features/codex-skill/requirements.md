---
status: active
last_reviewed: 2026-07-08
source_of_truth: product-intent
confidence: medium
---

# Requirements: codex-skill

## Summary

Codex skill 应该把通用 NOC 协议转成 Codex 可执行的工作流，优先让 Codex 通过机器可读 work plan 定位相关文档。

## Business Rules

- BR-001: 当代码可能变化时，已安装 Skill 优先使用 `noc work ... --json`。
- BR-002: 如果 JSON 输出不可用，允许 fallback 到文本 work plan。
- BR-003: 发布包内的 Skill 必须带有与 CLI 同版本的 NOC 管理清单，供 `noc setup` 安全安装和升级。

## Acceptance Criteria

- AC-001: skill 明确列出触发场景、执行步骤、停止条件和完成定义。
- AC-002: skill 引用的 reference 文件和 eval 文件必须存在。
- AC-003: 正式 Skill 及运行时 references 不依赖仓库内的 `python scripts/noc.py` 路径。
- AC-004: Definition of Done 必须分别约束 v2 simplified 和 v1 legacy 项目，不得要求 v2 创建 v1 文档类型。

## Non-Goals

- skill 本身不替代 CLI 的确定性检查。


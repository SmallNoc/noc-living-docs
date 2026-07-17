---
status: active
last_reviewed: 2026-07-08
source_of_truth: product-intent
confidence: medium
---

# Requirements: init-index-validate

## Summary

初始化、索引和校验命令应该让一个已有项目安全接入 NOC，并为 agent 提供可信的路由索引。

## Business Rules

- BR-001: 初始化必须保留已有 agent 文件中 managed block 之外的内容。
- BR-002: 索引应保留人工维护的 feature path 映射和额外元数据。

## Acceptance Criteria

- AC-001: 新项目执行不带 `--mode` 的 `noc init` 时生成 protocol v2 简化项目记忆并内部完成索引和健康检查。
- AC-002: `noc validate --target <project>` 能校验目标项目结构。
- AC-003: 显式 small/domain/auto 布局和已有 v1 项目继续使用 protocol v1，不自动迁移或删除七文档。
- AC-004: v2 初始化保留已有 README 和 AGENTS managed block 外内容，不编造无法从仓库确认的业务事实。
- AC-005: 旧 simplified 和 v1 small/domain 项目只能通过显式 `noc migrate` 迁移到 feature-archive；dry-run 必须零写入，apply 必须先备份完整 `noc_docs` 并重建派生索引。
- AC-006: v1 迁移必须保留原始文本，不能把 `status.md`、`notes.md` 或 `requirements.md` 机械提升为当前事实。

## Non-Goals

- 不迁移已有 `docs/` 内容，除非用户明确要求。
- 不在普通 `init/index/validate/doctor/work/check/evidence` 命令中静默升级旧 layout。


---
status: active
last_reviewed: 2026-07-17
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
- BR-004: feature-archive 项目中，Skill 必须通过 `noc work` 识别候选功能，高置信度自动选择，明确新业务功能通过 `noc feature ensure` 创建，歧义或低置信度只询问用户一次。
- BR-005: feature-archive 项目中，Skill 修改代码前必须读取项目级 `project.md`、`guardrails.md`、`verification.md` 和相关功能 `overview.md`，修改后通过真实验证、`noc evidence`、`noc evidence record`、`noc feature update` 和 `noc check --feature-impact-file` 完成闭环。
- BR-006: `language: zh-CN` 时，功能名称、overview 正文、验证摘要和最终汇报使用简体中文；JSON/YAML key、feature id、CLI 参数、路径、代码标识和命令保持英文或原文。

## Acceptance Criteria

- AC-001: skill 明确列出触发场景、执行步骤、停止条件和完成定义。
- AC-002: skill 引用的 reference 文件和 eval 文件必须存在。
- AC-003: 正式 Skill 及运行时 references 不依赖仓库内的 `python scripts/noc.py` 路径。
- AC-004: Definition of Done 必须分别约束 v2 simplified 和 v1 legacy 项目，不得要求 v2 创建 v1 文档类型。
- AC-005: 两份正式 Skill 必须包含同一套 feature-archive 自动工作流和安全限制，不得自由重写整个 `overview.md`、伪造测试通过、把计划写成当前实现或静默迁移旧布局。
- AC-006: simplified、small、domain 旧布局继续兼容，Skill 不自动创建 features 或迁移到 feature-archive。
- AC-007: release wheel 必须携带标准 `.agents` Skill 和兼容 `skills/codex` Skill 资产，且两份 runtime 内容保持同步。

## Non-Goals

- skill 本身不替代 CLI 的确定性检查。


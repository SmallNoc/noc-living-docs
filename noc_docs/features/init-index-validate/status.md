---
status: active
last_reviewed: 2026-07-08
source_of_truth: code
confidence: medium
---

# Current Status: init-index-validate

## Current Behavior

`noc init` 对未指定 `--mode` 的新项目生成 protocol v2 简化结构：三个项目级 Markdown 和记忆配置、路由、清单；它从 README、项目标志、源码和测试目录提取可确认事实，并保留已有 AGENTS 内容。显式 small/domain/auto 和已有 features/domains 项目仍走 v1 流程。`index`、`validate` 和 `doctor` 可识别两种协议，本仓库自身保持 v1。

阶段 1 feature-archive MVP 只增加只读识别：`validate` 可校验手工存在的 `layout: feature-archive`、`layout_version: "1.0"`、项目级三文件和 `features/<feature-id>/overview.md` frontmatter；`doctor` 可报告 feature-archive 布局状态。旧 simplified 项目的 `work/index/doctor/validate` 不创建 `features/`，不改 `routing.json`，不补写缺失的 `language` 字段。

阶段 2 将新项目默认初始化切换为 feature-archive layout。`noc init` 对全新项目创建项目级三文件、空的 `noc_docs/features/` 根目录，以及 `config.json`、`routing.json`、`manifest.json`、`feature-index.json`、`evidence-index.json`。不会创建示例业务功能目录。已有 `layout: simplified` 或 `layout: feature-archive` 的 v2 项目再次执行默认 `noc init` 时只返回 ready，不重建或覆盖已有内容。

`noc index` 现在可以从 Markdown 事实来源重建 feature-archive 派生 JSON。事实来源是 `project.md`、`guardrails.md`、`verification.md` 和 `features/*/overview.md`；派生数据是 `routing.json`、`manifest.json`、`feature-index.json` 和 `evidence-index.json`。删除派生 JSON 后重新执行 `noc index` 可恢复完整索引，重复执行保持幂等；索引失败时先校验 overview frontmatter，不覆盖已有派生索引。

阶段 3 中，`noc feature ensure` 在成功创建新功能 overview 后调用 feature-archive 索引重建，使 `feature-index.json` 立即包含新功能。`noc work` 依赖 `feature-index.json` 加载候选，但当该派生索引缺失或 JSON 损坏时，只读扫描 `features/*/overview.md` 作为 fallback，不重建索引、不修改 Markdown。

## Important Files

- `scripts/init-noc-docs.py`
- `scripts/index-noc-docs.py`
- `scripts/validate-noc-docs.py`
- `.agents/skills/project-living-docs/`
- `skills/codex/project-living-docs/`

## Data, API, or Configuration

- `noc_docs/.living-docs/config.json`
- `noc_docs/.living-docs/feature-map.json`
- v2: `config.json`、`routing.json`、`manifest.json`
- feature-archive stage 1: `config.json` 的 `protocol_version`、`layout`、`layout_version`、`language`、`machine_keys` 只被读取和校验；派生索引生成留给后续阶段。
- feature-archive stage 2: `feature-index.json` 在空功能集合时为 `{"schema_version": "1.0", "features": []}`；有 overview 时索引 `id`、`name`、`aliases`、`status`、`language`、`overview_path` 和 `updated_at`。
- feature-archive stage 3: candidate routing 使用索引和 overview 正文作为事实来源；索引缺失 fallback 是只读行为，不会隐式修复或升级项目。

## Known Issues

- `suggest-map` 对平铺 CLI 仓库可能返回空数组，这是允许的。


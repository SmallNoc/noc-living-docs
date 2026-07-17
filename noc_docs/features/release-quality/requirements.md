---
status: active
last_reviewed: 2026-07-17
source_of_truth: product-intent
confidence: medium
---

# Requirements: release-quality

## Summary

发布质量要求所有 CLI 行为、模板协议和 release bookkeeping 都有可重复验证方式。

## Business Rules

- BR-001: 新 CLI 行为必须有 unittest。
- BR-002: release 前必须通过 validate、release check、unittest 和 py_compile。
- BR-003: PyPI 发布必须使用 GitHub Actions Trusted Publishing，不在仓库、README 或 workflow 中保存 PyPI token、密码或 API key。
- BR-004: PyPI wheel 必须包含 `noc` entry point 和初始化所需的 `templates/noc_docs/` 文件。
- BR-005: PyPI wheel 必须包含 `project-living-docs` Skill、版本清单和正式运行所需 references。

## Acceptance Criteria

- AC-001: `python -m unittest discover -s tests` 通过，CI 不显式枚举测试模块。
- AC-002: `python scripts/release.py --check` 通过。
- AC-003: `python -m build` 生成 `.whl` 和 `.tar.gz`。
- AC-004: `python -m twine check dist/*` 通过，README 可作为 PyPI long description 渲染。
- AC-005: 从 wheel 安装后 `noc --help` 和 `noc init <target>` 可用。
- AC-006: 从 wheel 安装后 `noc setup` 可以向隔离的 `CODEX_HOME` 安装同版本 Skill。
- AC-007: README 首屏只呈现安装、一次初始化和正常使用 Codex 三步流程，内部命令移至工作原理或高级用法。
- AC-008: 仓库外隔离安装的 wheel 必须完成 version、setup、v2 init 幂等、语义 check 和中文空格路径验证。
- AC-009: README 默认流程和生成目录以 feature-archive 为主，说明每个功能默认一个目录和 `overview.md`，中文项目默认生成中文正文。
- AC-010: 两份运行时 Skill 内容同步，Definition of Done 分别约束 feature-archive、simplified 与 v1 legacy 项目。
- AC-011: setup 安装和 setup check 必须确认安装后的 Skill 与仓库正式 Skill 一致，且重复 setup 幂等、不安装 Git hook、不覆盖用户自定义同名 Skill。
- AC-012: release wheel 必须包含 `scripts.noclib` 全部运行模块、标准 `.agents` Skill 资产、兼容 `skills/codex` Skill 资产、templates 和必要 package data。

## Non-Goals

- 不在 release-quality 中实现业务功能。


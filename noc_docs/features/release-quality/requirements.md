---
status: active
last_reviewed: 2026-07-08
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

- AC-001: `python -m unittest tests.test_noc_cli tests.test_release_cli tests.test_setup_cli` 通过。
- AC-002: `python scripts/release.py --check` 通过。
- AC-003: `python -m build` 生成 `.whl` 和 `.tar.gz`。
- AC-004: `python -m twine check dist/*` 通过，README 可作为 PyPI long description 渲染。
- AC-005: 从 wheel 安装后 `noc --help` 和 `noc init <target>` 可用。
- AC-006: 从 wheel 安装后 `noc setup` 可以向隔离的 `CODEX_HOME` 安装同版本 Skill。
- AC-007: README 首屏只呈现安装、一次初始化和正常使用 Codex 三步流程，内部命令移至高级用法。
- AC-008: 仓库外隔离安装的 wheel 必须完成 version、setup、v2 init 幂等、语义 check 和中文空格路径验证。

## Non-Goals

- 不在 release-quality 中实现业务功能。


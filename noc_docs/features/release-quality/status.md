---
status: active
last_reviewed: 2026-07-17
source_of_truth: code
confidence: medium
---

# Current Status: release-quality

## Current Behavior

测试通过 Python unittest 和 pytest 运行，覆盖 CLI help、setup/init/index/check/doctor/work/feature lifecycle、Codex Skill 安装保护、release 脚本、PyPI publish workflow 和打包元数据。wheel 同时包含项目模板和带版本清单的 `project-living-docs` Skill 运行文件。当前准备版本为 `1.2.1`；本阶段不会创建 tag 或发布 PyPI。

PR 验证运行完整 tests discovery；tag 发布 workflow 在 wheel 安装后先执行 `noc setup`，再验证 simplified init，因此远程门禁覆盖 Skill 安装与新项目初始化闭环。

README 首屏现以安装、默认 v2 simplified 初始化、正常使用 Codex 三步作为唯一入门流程；主要示例和生成目录对应 v2 的三份项目记忆，v1 small/domain 与 feature lifecycle 保留在 Legacy v1 / Advanced compatibility。两份 Skill 的 Definition of Done 分开约束 v2 与 v1，Validate workflow 通过 unittest discovery 自动覆盖全部测试文件。wheel 隔离测试覆盖完整新用户旅程及语义记忆检查。

阶段 1 feature-archive MVP 新增 `scripts.noclib` 包，因此 wheel package list 现在包含 `scripts.noclib`，保证安装后的 `noc` CLI 可以导入 schema/layout helper。此更改不修改版本号、CHANGELOG、README、发布 workflow、tag 或 PyPI 发布流程。

阶段 2 wheel 验证覆盖安装后的 `noc init` 和 `noc index`，确认隔离环境中也能创建 feature-archive config 和四个派生索引。版本号仍为 `1.2.1`，本阶段未执行发布、打 tag 或修改 Trusted Publishing。

阶段 3 wheel 验证覆盖安装后的 `noc feature ensure`、`noc index` 和 `noc work --intent --json`，确认 `scripts.noclib.candidates` 与 `scripts.noclib.features` 已随 wheel 打包。版本号仍为 `1.2.1`，本阶段未执行发布、打 tag、合并或修改发布配置。

阶段 4 wheel 验证覆盖安装后的 `noc feature update`，确认 `scripts.noclib.feature_update` 已随 wheel 打包并可在隔离环境中更新 feature-archive overview。版本号仍为 `1.2.1`，本阶段未执行发布、打 tag、合并或修改 Trusted Publishing。

阶段 7 README 首屏改为安装、`noc init .` 和正常描述需求三步，默认流程指向 feature-archive，并把内部 CLI 放入高级说明。README 现在明确新项目默认 feature-archive、每个功能默认目录与 `overview.md`、中文项目默认中文正文、NOC 不伪造测试结果、旧项目不会静默迁移且 v1 small/domain 继续兼容。

setup 覆盖已扩展到安装 Skill 与仓库正式 Skill 逐文件一致、重复执行幂等、不安装 Git hook、用户自定义同名 Skill 不被覆盖；CLI fixture 覆盖 init、work、ensure、update、evidence、evidence record 和 feature impact check 的受控完整闭环。

## Important Files

- `tests/test_noc_cli.py`
- `tests/test_release_cli.py`
- `scripts/release.py`
- `pyproject.toml`
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `docs/release.md`
- `.github/workflows/publish.yml`
- `.gitignore`
- `.agents/skills/project-living-docs/`
- `tests/test_setup_cli.py`

## Data, API, or Configuration

- Python package entry point: `noc = "scripts.noc:main"`
- Python packages: `scripts`、`scripts.noclib`、`templates`、`noc_assets.project_living_docs`
- feature-archive 初始化、索引、候选识别、ensure 和 structured update helper 位于 `scripts.noclib.overview`、`scripts.noclib.indexes`、`scripts.noclib.candidates`、`scripts.noclib.features` 与 `scripts.noclib.feature_update`，已包含在 wheel 包中。
- `README.md` 是项目主要产品入口，归入 release-quality 路由。
- `pyproject.toml` package version 当前为 `1.2.1`，与 `VERSION`、README、CHANGELOG 和 Skill 清单保持一致。
- `pyproject.toml` 使用 SPDX license expression、`license-files = ["LICENSE"]`、显式 package data，确保 wheel 包含 `templates/noc_docs/.living-docs/*.json` 且不包含 `__pycache__`。
- `.github/workflows/publish.yml` 使用 `permissions.contents: read` 和 `permissions.id-token: write`，environment 为 `pypi`，不使用 token secret。
- wheel 内的 Skill package 路径为 `noc_assets/project_living_docs/`，安装目标为 `$CODEX_HOME/skills/project-living-docs/`；集成测试从仓库外工作目录启动隔离 venv，避免源码路径遮蔽 wheel。
- Stage 7 未修改 `VERSION` 或 `CHANGELOG.md`。

## Known Issues

- 无专门集成测试模拟真实 Codex 会话；主要通过 CLI subprocess 和文本断言覆盖。


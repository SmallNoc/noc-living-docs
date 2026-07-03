# NOC Living Docs

中文 | [English](#english)

NOC Living Docs 是一套面向 AI 编程 Agent 的活文档协议。

它为项目提供稳定的文档结构，让 Codex、Claude Code、Gemini CLI 或其他 Agent 在修改代码前，可以理解项目现状、功能需求、禁止操作、测试要求和改造历史。

## 核心理念

- 文档根目录固定为 `noc_docs/`。
- 默认中文正文，方便中文团队维护。
- 机器可识别结构保持英文：文件名、标题、编号、JSON key、状态值和命令。
- 小项目使用 `noc_docs/features/`。
- 大项目使用 `noc_docs/domains/<domain>/features/`。
- Agent 默认只读取受影响功能或业务域的相关文档，避免浪费上下文 token。
- 已有 `AGENTS.md`、`CLAUDE.md` 或 `GEMINI.md` 必须合并，不能覆盖。

## 仓库结构

```text
protocol/       与具体 Agent 无关的通用协议
templates/      AGENTS.md 和 noc_docs/ 项目模板
skills/         面向具体 Agent 的 skill 适配层
scripts/        初始化、索引、校验和 Git hook 工具
examples/       小项目和大项目示例
```

## 快速开始

初始化一个项目：

```bash
python scripts/noc.py init /path/to/project
python scripts/noc.py validate --target /path/to/project
```

然后告诉你的 Agent：

```text
Initialize NOC Living Docs for this project.
```

如果使用 Codex，可以安装或引用：

```text
skills/codex/project-living-docs
```

## 脚本命令

推荐统一入口：

```bash
python scripts/noc.py <command>
```

### 初始化

```bash
python scripts/noc.py init /path/to/project
```

选项：

- `--mode auto|small|domain`
- `--agent-file AGENTS.md|CLAUDE.md|GEMINI.md`
- `--force` 覆盖 `noc_docs/` 内已有文件
- `--no-index` 初始化后跳过索引生成

`auto` 会识别常见 monorepo marker、3 个以上 app/service 目录，以及 3 个以上带 `pom.xml`、`package.json`、`go.mod`、`pyproject.toml` 等项目标记的顶层项目目录。

初始化脚本不会覆盖已有 Agent 规则。它只会添加或更新以下受控区块：

```md
<!-- noc-living-docs:start -->
<!-- noc-living-docs:end -->
```

### 索引

```bash
python scripts/noc.py index /path/to/project
```

生成：

```text
noc_docs/.living-docs/manifest.json
noc_docs/.living-docs/docs-index.json
noc_docs/.living-docs/feature-map.json
```

Agent 应该先使用这些索引做路由，再读取最小必要范围的源文档。

`feature-map.json` 还会记录每个 feature 的文档可信度信号：

- `paths`：代码路径到 feature 的映射。
- `freshness.last_doc_update`：该 feature 源文档最近更新时间。
- `completeness.missing_docs`：缺失的标准 feature 文档。
- `completeness.complete`：是否具备完整标准文档集合。

### 校验

校验本仓库：

```bash
python scripts/noc.py validate
```

校验一个使用该协议的项目：

```bash
python scripts/noc.py validate --target /path/to/project
```

### Git Hook

安装 pre-commit hook，用来提示代码变更是否同步包含 NOC 文档变更：

```bash
python scripts/noc.py hook install /path/to/project
```

其他 hook 命令：

```bash
python scripts/noc.py hook status /path/to/project
python scripts/noc.py hook uninstall /path/to/project
```

### 变更检查

手动运行同样的检查：

```bash
python scripts/noc.py check /path/to/project --staged
```

默认情况下，手动运行 `check` 时，如果 staged 代码变更没有对应 staged `noc_docs/` 变更，该命令会失败。需要只提示不失败时，可以使用 `--warn-only`。

`check` 会识别常见代码、配置、SQL、Shell、Dockerfile、Java、Go、Tcl、SKILL 等工程文件。对于已经映射到 feature 的代码路径，它会要求 staged 文档变更命中对应 feature 的文档；仅修改无关 `noc_docs/` 文件不会被视为覆盖。

当检测到 SQL、Docker、CI、security、API 等路径或文件类型时，`check` 会输出轻量提示，建议检查 `status.md`、`test-record.md`、`guardrails.md`、`requirements.md` 或 `development/testing.md`。这是提示，不是静态分析器。

通过 `hook install` 安装的 pre-commit hook 默认使用 `--warn-only`，因此它会提示风险，但不会阻断提交。

### 映射建议

`suggest-map` 会扫描常见代码目录并输出 feature path 映射建议，但不会写入文件：

```bash
python scripts/noc.py suggest-map /path/to/project
```

确认建议可靠后，可以自动合并进 `feature-map.json`：

```bash
python scripts/noc.py suggest-map /path/to/project --write
```

`--write` 只会追加缺失的 path，不会覆盖已有人工维护的字段。你也可以手动把确认后的建议写入：

```text
noc_docs/.living-docs/feature-map.json
```

### 发布检查

版本号以 `VERSION` 为准，发布记录写入 `CHANGELOG.md`，Git tag 使用 `vX.Y.Z`：

```bash
python scripts/release.py --check
python scripts/release.py --bump patch
python scripts/release.py --version 1.0.0
```

`--check` 会校验：

- `VERSION` 使用 `MAJOR.MINOR.PATCH`。
- `CHANGELOG.md` 包含对应版本条目。
- 如果当前提交正好位于 Git tag 上，tag 必须等于 `v<VERSION>`。

CI 会在 push、PR 和 tag 场景运行发布检查、协议校验和测试。

推荐发布流程：

```bash
python scripts/release.py --version 1.0.0
python scripts/release.py --check
python -m unittest tests.test_noc_cli tests.test_release_cli
git add VERSION CHANGELOG.md README.md scripts tests .github
git commit -m "chore: prepare v1.0.0 release"
git tag -a v1.0.0 -m "v1.0.0"
git push origin main
git push origin v1.0.0
```

如果 `CHANGELOG.md` 有 `Unreleased` 内容，`release.py --version` 会把它移动到目标版本条目下，并保留空的 `Unreleased` 区块。

### 迁移测试

测试套件覆盖接近真实项目的迁移场景：

- 已有 `AGENTS.md` 时只追加或更新 NOC managed block，不覆盖用户规则。
- 已有 `docs/` 时保持原样，NOC 协议仍固定使用 `noc_docs/`。
- monorepo、3 个以上 app/service、或 3 个以上顶层项目目录自动进入 Domain Mode。
- YAML、SQL、Shell、Dockerfile、Java、Go、Tcl、SKILL 等工程文件变更会触发文档同步检查。

真实项目 dogfood 结果记录到：

```text
docs/migration-reports/YYYY-MM-DD-<repo>.md
```

## 文档根目录

`noc_docs/` 是协议固定根目录。不要为这套协议创建 `docs/`。如果项目已经有 `docs/`，除非用户明确要求迁移，否则保持不动。

## 语言策略

默认配置：

```json
{
  "language": "zh-CN",
  "machine_keys": "en-US"
}
```

这表示：正文默认中文，结构保持英文，以便 Agent、脚本和跨项目协作稳定解析。

## 状态

当前是 v1.0.0 小而硬的稳定协议版本，包含初始化、索引、校验、Git hook、相关文档检查、feature-map 建议、轻量变更提示和真实项目迁移报告。

---

## English

[中文](#noc-living-docs) | English

NOC Living Docs is a living documentation protocol for AI coding agents.

It gives projects a stable documentation structure that helps Codex, Claude Code, Gemini CLI, or other agents understand current behavior, requirements, guardrails, testing expectations, and change history before modifying code.

## Core Ideas

- The documentation root is always `noc_docs/`.
- Human-facing prose can be written in Chinese by default.
- Machine-facing structure stays English: file names, headings, IDs, JSON keys, status values, and commands.
- Small projects use `noc_docs/features/`.
- Large projects use `noc_docs/domains/<domain>/features/`.
- Agents should read only the relevant docs for the affected feature or domain.
- Existing `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` files must be merged, not overwritten.

## Repository Layout

```text
protocol/       Agent-neutral protocol documents
templates/      Project templates for AGENTS.md and noc_docs/
skills/         Agent-specific skill adapters
scripts/        Initialization, indexing, validation, and Git hook tools
examples/       Small-project and domain-project examples
```

## Quick Start

Initialize a project:

```bash
python scripts/noc.py init /path/to/project
python scripts/noc.py validate --target /path/to/project
```

Then ask your agent:

```text
Initialize NOC Living Docs for this project.
```

For Codex, install or reference:

```text
skills/codex/project-living-docs
```

## Commands

The recommended entry point is:

```bash
python scripts/noc.py <command>
```

### Initialize

```bash
python scripts/noc.py init /path/to/project
```

Options:

- `--mode auto|small|domain`
- `--agent-file AGENTS.md|CLAUDE.md|GEMINI.md`
- `--force` to overwrite existing files inside `noc_docs/`
- `--no-index` to skip index generation after init

`auto` detects common monorepo markers, 3 or more app/service directories, and 3 or more top-level project directories with markers such as `pom.xml`, `package.json`, `go.mod`, or `pyproject.toml`.

The initializer never overwrites existing agent rules. It adds or updates only the managed block between:

```md
<!-- noc-living-docs:start -->
<!-- noc-living-docs:end -->
```

### Index

```bash
python scripts/noc.py index /path/to/project
```

This generates:

```text
noc_docs/.living-docs/manifest.json
noc_docs/.living-docs/docs-index.json
noc_docs/.living-docs/feature-map.json
```

Agents should use these files for routing, then read the smallest relevant source documents.

`feature-map.json` also records trust signals for each feature:

- `paths`: code path mappings for the feature.
- `freshness.last_doc_update`: latest source documentation update for that feature.
- `completeness.missing_docs`: missing standard feature documents.
- `completeness.complete`: whether the feature has the complete standard document set.

### Validate

Validate this repository:

```bash
python scripts/noc.py validate
```

Validate a project using the protocol:

```bash
python scripts/noc.py validate --target /path/to/project
```

### Git Hook

Install a pre-commit hook that warns when code changes are not accompanied by NOC docs changes:

```bash
python scripts/noc.py hook install /path/to/project
```

Other hook commands:

```bash
python scripts/noc.py hook status /path/to/project
python scripts/noc.py hook uninstall /path/to/project
```

### Change Check

Run the same check manually:

```bash
python scripts/noc.py check /path/to/project --staged
```

By default, the manual `check` command exits with failure when staged code changes have no staged `noc_docs/` changes. Use `--warn-only` when you want advisory output only.

`check` recognizes common code, config, SQL, shell, Dockerfile, Java, Go, Tcl, SKILL, and related engineering files. For code paths mapped to a feature, staged documentation changes must touch that affected feature's docs; unrelated `noc_docs/` edits do not count as coverage.

When SQL, Docker, CI, security, or API-looking paths are detected, `check` prints lightweight hints suggesting `status.md`, `test-record.md`, `guardrails.md`, `requirements.md`, or `development/testing.md`. This is advisory, not a static analyzer.

The pre-commit hook installed by `hook install` uses `--warn-only` by default, so it warns about risk without blocking commits.

### Mapping Suggestions

`suggest-map` scans common code directories and prints feature path mapping suggestions without writing files:

```bash
python scripts/noc.py suggest-map /path/to/project
```

After review, merge suggestions into `feature-map.json`:

```bash
python scripts/noc.py suggest-map /path/to/project --write
```

`--write` only appends missing paths. It does not overwrite manually maintained fields. You can also copy useful suggestions into:

```text
noc_docs/.living-docs/feature-map.json
```

### Release Check

`VERSION` is the source of truth for the project version. Release notes live in `CHANGELOG.md`, and Git tags use `vX.Y.Z`:

```bash
python scripts/release.py --check
python scripts/release.py --bump patch
python scripts/release.py --version 1.0.0
```

`--check` validates that:

- `VERSION` uses `MAJOR.MINOR.PATCH`.
- `CHANGELOG.md` contains an entry for the version.
- If the current commit is exactly on a Git tag, that tag matches `v<VERSION>`.

CI runs release checks, protocol validation, and tests on pushes, pull requests, and tags.

Recommended release flow:

```bash
python scripts/release.py --version 1.0.0
python scripts/release.py --check
python -m unittest tests.test_noc_cli tests.test_release_cli
git add VERSION CHANGELOG.md README.md scripts tests .github
git commit -m "chore: prepare v1.0.0 release"
git tag -a v1.0.0 -m "v1.0.0"
git push origin main
git push origin v1.0.0
```

If `CHANGELOG.md` has `Unreleased` content, `release.py --version` moves it into the target version entry and keeps an empty `Unreleased` section.

### Migration Tests

The test suite covers realistic migration cases:

- Existing `AGENTS.md` content is preserved while the NOC managed block is appended or updated.
- Existing `docs/` directories are left untouched; the protocol still uses fixed `noc_docs/`.
- Monorepos, projects with 3 or more apps/services, or projects with 3 or more top-level project directories automatically use Domain Mode.
- YAML, SQL, shell, Dockerfile, Java, Go, Tcl, SKILL, and related engineering changes trigger documentation sync checks.

Record real-project dogfood results in:

```text
docs/migration-reports/YYYY-MM-DD-<repo>.md
```

## Documentation Root

`noc_docs/` is fixed by the protocol. Do not create `docs/` for this system. If a project already has `docs/`, leave it untouched unless the user explicitly asks for migration.

## Language Policy

Default mode:

```json
{
  "language": "zh-CN",
  "machine_keys": "en-US"
}
```

This means prose is Chinese by default, while structure remains English for stable parsing and cross-agent use.

## Status

This repository is the small-but-hard v1.0.0 protocol release with initialization, indexing, validation, Git hook, related-document checks, feature-map suggestions, lightweight change hints, and real-project migration reports.

# NOC Living Docs

![CI](https://github.com/SmallNoc/noc-living-docs/actions/workflows/ci.yml/badge.svg)
![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-yellow.svg)
![Codex Skill](https://img.shields.io/badge/Codex-Skill-blue)
![Living Docs](https://img.shields.io/badge/Living%20Docs-NOC-green)

A Codex skill and local CLI that keeps requirements, current behavior, guardrails, tests, and change records synchronized with code changes.

NOC is a lightweight **agent memory router** for codebases.

It helps AI coding agents find the smallest useful project context before they edit code, then leave behind the facts that future sessions need: current behavior, requirements, guardrails, tests, and important changes.

NOC is intentionally local and small. It does not call a model, run a server, replace your issue tracker, or try to become a wiki.

中文说明在下方：[中文](#中文)。

**License note:** you can read and use this for learning, research, and personal non-commercial work. Commercial use needs written permission.

## Why NOC

AI coding agents are fast, but project memory is fragile.

Common failure modes:

- Requirements stay in chat and disappear with the session.
- Current behavior is buried in code, old PRs, or someone's memory.
- Guardrails get forgotten when a new agent starts fresh.
- Test commands and gaps are not recorded.
- Agents read too much, miss the important file, or confidently infer the wrong thing.

NOC gives each feature a stable documentation home and gives agents one deterministic first step:

```bash
noc work . --path src/auth/login.py --json
```

That command answers: what feature is this, how confident is the mapping, which docs should I read, and what should I update after the code changes?

## What It Looks Like

Given a path like `scripts/noc.py`, NOC can return a work plan like this:

```json
{
  "schema_version": "1.0",
  "resolution_status": "resolved",
  "paths": ["scripts/noc.py"],
  "features": [
    {
      "id": "cli-core",
      "matched_by": "path",
      "matched_pattern": "scripts/noc.py",
      "confidence": "high",
      "read_before_code": [
        "noc_docs/features/cli-core/agent-guide.md",
        "noc_docs/features/cli-core/status.md",
        "noc_docs/features/cli-core/guardrails.md",
        "noc_docs/features/cli-core/test-record.md"
      ],
      "update_after_code": [
        {
          "doc": "noc_docs/features/cli-core/status.md",
          "reason": "when actual behavior changes"
        },
        {
          "doc": "noc_docs/features/cli-core/test-record.md",
          "reason": "with verification commands and results"
        }
      ]
    }
  ],
  "next_actions": []
}
```

If NOC cannot resolve a path, it says so explicitly with `resolution_status: "unresolved"` and suggests the next command, such as `noc suggest-map` or `noc feature create`.

## Install

Current recommended install from source:

```bash
pipx install git+https://github.com/SmallNoc/noc-living-docs.git
noc --help
```

After the package is published to PyPI, use:

```bash
pipx install noc-living-docs
noc --help
```

For local development without installing:

```bash
git clone https://github.com/SmallNoc/noc-living-docs.git
cd noc-living-docs
python scripts/noc.py --help
```

## Update

If installed with `pipx`:

```bash
pipx upgrade noc-living-docs
```

If installed with `pip`:

```bash
python -m pip install --upgrade noc-living-docs
```

If running from source:

```bash
git pull
python scripts/noc.py --help
```

After updating an existing NOC-enabled project, refresh indexes:

```bash
noc index /path/to/project
noc doctor /path/to/project
```

## Quick Start

Add NOC to a project:

```bash
noc init /path/to/project
noc doctor /path/to/project
```

Create docs for a real feature and map code to it:

```bash
noc feature create /path/to/project user-login --path src/auth/
```

Before changing code, route the agent:

```bash
noc work /path/to/project --path src/auth/login.py --json
```

Or route from Git state:

```bash
noc work /path/to/project --staged --json
noc work /path/to/project --changed --json
```

After changing code, update only the facts that changed, then verify:

```bash
noc index /path/to/project
noc check /path/to/project --staged
```

## Daily Use

Use this loop for normal feature work:

1. Run `noc work <project> --path <code/path> --json`.
2. Read only the docs listed in `read_before_code`.
3. Change code.
4. Update only the docs whose facts changed.
5. Run `noc index <project>`.
6. Run `noc check <project> --staged`.

Use this loop when changes are already in Git:

```bash
noc work . --changed --json
noc work . --staged --json
```

Use this loop when NOC cannot resolve a path:

```bash
noc suggest-map . --interactive
noc feature create . <feature> --path <code/path>
noc index .
```

## Agent Workflow

Before code:

1. Run `noc work <project> --path <code/path> --json`, or use `--staged` / `--changed`.
2. Read only the docs listed in the work plan.
3. Stop and ask if a requested change conflicts with `guardrails.md`.
4. Put confirmed new intent in `requirements.md`; put uncertainty in `notes.md`.

After code:

1. Update `status.md` when actual behavior changed.
2. Update `test-record.md` with commands, results, and gaps.
3. Update `change-record.md` for important changes worth remembering.
4. Update `requirements.md` only when intended behavior changed.
5. Run `noc index` and `noc check --staged`.

The point is not to update every file every time. The point is to keep the few facts future agents will need.

## Commands

| Command | What it does |
|---|---|
| `noc init <project>` | Adds `noc_docs/` and an agent entry block. |
| `noc doctor <project>` | Checks setup, JSON, Git, mode, indexes, and hook state. |
| `noc work <project>` | Routes a feature, path, or Git diff to the docs an agent should read and update. Use `--json` for automation. |
| `noc check <project>` | Warns or fails when code changed without matching NOC docs. |
| `noc index <project>` | Refreshes generated `.living-docs` routing files. |
| `noc suggest-map <project>` | Suggests code-path to feature mappings. |
| `noc feature create <project> <feature>` | Creates a feature doc folder from the template. |
| `noc feature adopt <project> <source> <feature>` | Turns a placeholder feature folder into a real one. |
| `noc feature rename <project> <old> <new>` | Renames a feature folder and its mapping. |
| `noc hook install <project>` | Installs the pre-commit reminder. |
| `noc hook status <project>` | Shows whether the pre-commit reminder is installed. |
| `noc hook uninstall <project>` | Removes the NOC managed hook block. |
| `noc validate --target <project>` | Validates a target project. |
| `noc validate` | Validates this repository. |

Use `noc <command> --help` for arguments.

## Generated Documents

Default `small` mode creates:

```text
<project>/
  AGENTS.md
  noc_docs/
    docs-map.md
    project-status.md
    development/
      documentation-policy.md
      git-workflow.md
      testing.md
    features/
      index.md
      _feature/
        agent-guide.md
        requirements.md
        status.md
        guardrails.md
        test-record.md
        change-record.md
        notes.md
    .living-docs/
      config.json
      docs-index.json
      feature-map.json
      manifest.json
```

`AGENTS.md` can be replaced by `CLAUDE.md` or `GEMINI.md`:

```bash
noc init /path/to/project --agent-file CLAUDE.md
noc init /path/to/project --agent-file GEMINI.md
```

`_feature/` is a template placeholder. Real feature docs are created with:

```bash
noc feature create /path/to/project user-login --path src/auth/
```

That creates:

```text
noc_docs/features/user-login/
  agent-guide.md
  requirements.md
  status.md
  guardrails.md
  test-record.md
  change-record.md
  notes.md
```

## Document Responsibilities

| File | Purpose |
|---|---|
| `docs-map.md` | Tells humans and agents where to start. |
| `project-status.md` | Summarizes the project, stack, capabilities, and known risks. |
| `development/documentation-policy.md` | Explains how docs should be maintained. |
| `development/git-workflow.md` | Records Git and commit expectations. |
| `development/testing.md` | Records expected verification commands. |
| `features/index.md` | Lists feature documentation folders. |
| `agent-guide.md` | Quick entry point for a feature. |
| `requirements.md` | Intended behavior, business rules, and acceptance criteria. |
| `status.md` | Current behavior as implemented. |
| `guardrails.md` | Constraints that must not be broken. |
| `test-record.md` | Test strategy, commands, results, and gaps. |
| `change-record.md` | Important changes and why they happened. |
| `notes.md` | Temporary notes, open questions, and uncertain findings. |

## Machine Files

The `.living-docs/` directory is generated and maintained by `noc index`.

| File | Purpose |
|---|---|
| `config.json` | Project mode and check strictness configuration. |
| `feature-map.json` | Maps code paths to feature docs and stores trust signals. |
| `docs-index.json` | Lists known documentation files and metadata. |
| `manifest.json` | Records generated file inventory for validation. |

Agents should read `feature-map.json` through `noc work --json` rather than parsing it by hand.

## Domain Mode

Bigger projects can use domain mode:

```bash
noc init /path/to/project --mode domain
```

Domain mode creates:

```text
noc_docs/
  domains/
    index.md
    _domain/
      index.md
      guardrails.md
      features/
        _feature/
          agent-guide.md
          requirements.md
          status.md
          guardrails.md
          test-record.md
          change-record.md
          notes.md
```

Use domain mode for monorepos, multi-service systems, or teams with domain-level guardrails.

## How It Compares

| Tool | Good for | NOC's role |
|---|---|---|
| README | Project overview and setup | Points agents to feature-level memory before a change. |
| Wiki or docs site | Long-form guides and broad knowledge | Keeps change-critical memory next to the code workflow. |
| ADRs | Architectural decisions | Records feature behavior, guardrails, tests, and change facts. |
| Issue tracker | Planning, ownership, and discussion | Preserves what became true after implementation. |
| Generated API docs | Reference generated from code | Captures intent, constraints, and verification that code alone does not show. |

NOC can coexist with all of these. It is the local routing layer that tells an agent where to look before it edits code.

## For Coding Agents

Codex can use the bundled skill from the standard skill path:

```text
.agents/skills/project-living-docs
```

Project install:

```bash
mkdir -p /path/to/project/.agents/skills
cp -R .agents/skills/project-living-docs /path/to/project/.agents/skills/
```

Global install:

```bash
mkdir -p ~/.agents/skills
cp -R .agents/skills/project-living-docs ~/.agents/skills/
```

The legacy repo path `skills/codex/project-living-docs` is kept for compatibility, but `.agents/skills/project-living-docs` is the path new Codex users should copy.

Generic agents can read the managed block from:

```bash
noc init /path/to/project --agent-file AGENTS.md
```

See [Agent Compatibility](docs/agent-compatibility.md) for details.

## Developing This Repo

```bash
python scripts/noc.py validate
python scripts/release.py --check
python -m unittest tests.test_noc_cli tests.test_release_cli
```

```bash
python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py
```

Current version: `1.0.1`.

## GitHub Discovery

Suggested GitHub topics:

```text
codex
codex-skill
agent-skills
ai-coding
agents-md
living-docs
developer-tools
documentation
cli
git-hooks
project-memory
```

More reading:

- [Why NOC](docs/why-noc.md)
- [Agent Compatibility](docs/agent-compatibility.md)
- [Comparisons](docs/comparisons.md)
- [v1 Readiness](docs/v1-readiness.md)
- [Migration Reports](docs/migration-reports/)

## License

This repo is source-available and non-commercial by default.

Code, scripts, templates, and skills are licensed under the PolyForm Noncommercial License 1.0.0. For commercial use, get written permission first.

---

## 中文

NOC 是一个 Codex skill 和本地 CLI，用来让需求、当前行为、guardrails、测试和变更记录随代码改动保持同步。

NOC 是给代码仓库用的轻量级 **agent memory router**。

它帮助 AI 编程助手在改代码前找到最小但有用的项目上下文，并在改完后留下未来会话需要的事实：当前行为、需求、限制、测试和重要变更。

NOC 保持本地、小而硬。它不调用模型、不运行服务端、不替代 issue tracker，也不试图变成 Wiki。

## 为什么需要 NOC

AI agent 写代码很快，但项目记忆很容易丢：

- 需求留在聊天里，换会话就消失。
- 当前行为藏在代码、旧 PR 或某个人的记忆里。
- guardrails 被新会话忘掉。
- 测试命令和测试缺口没有沉淀。
- agent 读太多、读错文件，或者自信地猜错。

NOC 给每个功能一个稳定的文档位置，也给 agent 一个确定的第一步：

```bash
noc work . --path src/auth/login.py --json
```

这个命令会回答：这是什么 feature、映射置信度如何、应该先读哪些文档、改完后可能要更新什么。

## 效果示例

给定 `scripts/noc.py` 这样的路径，NOC 可以返回这样的 work plan：

```json
{
  "schema_version": "1.0",
  "resolution_status": "resolved",
  "paths": ["scripts/noc.py"],
  "features": [
    {
      "id": "cli-core",
      "matched_by": "path",
      "matched_pattern": "scripts/noc.py",
      "confidence": "high",
      "read_before_code": [
        "noc_docs/features/cli-core/agent-guide.md",
        "noc_docs/features/cli-core/status.md",
        "noc_docs/features/cli-core/guardrails.md",
        "noc_docs/features/cli-core/test-record.md"
      ],
      "update_after_code": [
        {
          "doc": "noc_docs/features/cli-core/status.md",
          "reason": "when actual behavior changes"
        },
        {
          "doc": "noc_docs/features/cli-core/test-record.md",
          "reason": "with verification commands and results"
        }
      ]
    }
  ],
  "next_actions": []
}
```

如果 NOC 无法解析路径，它会明确返回 `resolution_status: "unresolved"`，并建议下一步命令，例如 `noc suggest-map` 或 `noc feature create`。

## 安装

当前推荐从源码安装：

```bash
pipx install git+https://github.com/SmallNoc/noc-living-docs.git
noc --help
```

PyPI 发布后再使用：

```bash
pipx install noc-living-docs
noc --help
```

本地开发不安装时：

```bash
git clone https://github.com/SmallNoc/noc-living-docs.git
cd noc-living-docs
python scripts/noc.py --help
```

## 更新

如果使用 `pipx` 安装：

```bash
pipx upgrade noc-living-docs
```

如果使用 `pip` 安装：

```bash
python -m pip install --upgrade noc-living-docs
```

如果使用源码：

```bash
git pull
python scripts/noc.py --help
```

已有项目升级后，刷新索引：

```bash
noc index /path/to/project
noc doctor /path/to/project
```

## 快速开始

给项目接入 NOC：

```bash
noc init /path/to/project
noc doctor /path/to/project
```

创建真实 feature 并映射代码路径：

```bash
noc feature create /path/to/project user-login --path src/auth/
```

改代码前，先路由 agent：

```bash
noc work /path/to/project --path src/auth/login.py --json
```

或者从 Git 状态路由：

```bash
noc work /path/to/project --staged --json
noc work /path/to/project --changed --json
```

改完代码后，只更新真的变化了的事实，然后验证：

```bash
noc index /path/to/project
noc check /path/to/project --staged
```

## 日常使用

普通功能开发使用这个循环：

1. 运行 `noc work <project> --path <code/path> --json`。
2. 只读 `read_before_code` 列出的文档。
3. 修改代码。
4. 只更新事实发生变化的文档。
5. 运行 `noc index <project>`。
6. 运行 `noc check <project> --staged`。

如果代码已经改了，可以从 Git 状态生成 work plan：

```bash
noc work . --changed --json
noc work . --staged --json
```

如果 NOC 无法解析路径：

```bash
noc suggest-map . --interactive
noc feature create . <feature> --path <code/path>
noc index .
```

## Agent 工作流

改代码前：

1. 运行 `noc work <project> --path <code/path> --json`，或者用 `--staged` / `--changed`。
2. 只读 work plan 里列出的文档。
3. 如果请求和 `guardrails.md` 冲突，停下来问用户。
4. 已确认的新意图写进 `requirements.md`；不确定的问题写进 `notes.md`。

改代码后：

1. 当前行为变了，更新 `status.md`。
2. 写入测试命令、结果和缺口到 `test-record.md`。
3. 重要变更写进 `change-record.md`。
4. 只有目标行为变了，才更新 `requirements.md`。
5. 运行 `noc index` 和 `noc check --staged`。

重点不是每次更新所有文件，而是保留未来 agent 真正需要的少数事实。

## 命令

| 命令 | 作用 |
|---|---|
| `noc init <project>` | 添加 `noc_docs/` 和 agent 入口区块。 |
| `noc doctor <project>` | 检查环境、JSON、Git、模式、索引和 hook 状态。 |
| `noc work <project>` | 根据 feature、路径或 Git diff 路由到 agent 应该读和更新的文档。自动化场景使用 `--json`。 |
| `noc check <project>` | 检查代码变更是否缺少对应 NOC 文档更新。 |
| `noc index <project>` | 刷新 `.living-docs` 里的路由文件。 |
| `noc suggest-map <project>` | 建议代码路径到 feature 的映射。 |
| `noc feature create <project> <feature>` | 从模板创建 feature 文档目录。 |
| `noc feature adopt <project> <source> <feature>` | 把占位 feature 目录转成真实 feature。 |
| `noc feature rename <project> <old> <new>` | 重命名 feature 目录和映射。 |
| `noc hook install <project>` | 安装 pre-commit 提醒。 |
| `noc hook status <project>` | 查看 pre-commit 提醒是否安装。 |
| `noc hook uninstall <project>` | 移除 NOC managed hook 区块。 |
| `noc validate --target <project>` | 校验目标项目。 |
| `noc validate` | 校验本仓库。 |

参数细节可运行 `noc <command> --help`。

## 生成的文档

默认 `small` 模式会生成：

```text
<project>/
  AGENTS.md
  noc_docs/
    docs-map.md
    project-status.md
    development/
      documentation-policy.md
      git-workflow.md
      testing.md
    features/
      index.md
      _feature/
        agent-guide.md
        requirements.md
        status.md
        guardrails.md
        test-record.md
        change-record.md
        notes.md
    .living-docs/
      config.json
      docs-index.json
      feature-map.json
      manifest.json
```

`AGENTS.md` 可以替换成 `CLAUDE.md` 或 `GEMINI.md`：

```bash
noc init /path/to/project --agent-file CLAUDE.md
noc init /path/to/project --agent-file GEMINI.md
```

`_feature/` 是模板占位目录。真实 feature 文档用下面的命令创建：

```bash
noc feature create /path/to/project user-login --path src/auth/
```

会生成：

```text
noc_docs/features/user-login/
  agent-guide.md
  requirements.md
  status.md
  guardrails.md
  test-record.md
  change-record.md
  notes.md
```

## 文档职责

| 文件 | 作用 |
|---|---|
| `docs-map.md` | 告诉人和 agent 从哪里开始读。 |
| `project-status.md` | 总结项目、技术栈、当前能力和已知风险。 |
| `development/documentation-policy.md` | 说明文档维护规则。 |
| `development/git-workflow.md` | 记录 Git 和提交期望。 |
| `development/testing.md` | 记录验证命令和测试要求。 |
| `features/index.md` | 列出 feature 文档目录。 |
| `agent-guide.md` | 某个 feature 的快速入口。 |
| `requirements.md` | 目标行为、业务规则和验收标准。 |
| `status.md` | 当前代码实际行为。 |
| `guardrails.md` | 不能破坏的限制。 |
| `test-record.md` | 测试策略、命令、结果和缺口。 |
| `change-record.md` | 重要变更及原因。 |
| `notes.md` | 临时笔记、开放问题和不确定发现。 |

## 机器文件

`.living-docs/` 目录由 `noc index` 生成和维护。

| 文件 | 作用 |
|---|---|
| `config.json` | 项目模式和 check 严格度配置。 |
| `feature-map.json` | 把代码路径映射到 feature 文档，并保存 trust signals。 |
| `docs-index.json` | 列出已知文档和元数据。 |
| `manifest.json` | 记录生成文件清单，供校验使用。 |

agent 应该通过 `noc work --json` 使用 `feature-map.json`，而不是手写解析它。

## Domain 模式

大项目可以使用 domain 模式：

```bash
noc init /path/to/project --mode domain
```

domain 模式生成：

```text
noc_docs/
  domains/
    index.md
    _domain/
      index.md
      guardrails.md
      features/
        _feature/
          agent-guide.md
          requirements.md
          status.md
          guardrails.md
          test-record.md
          change-record.md
          notes.md
```

monorepo、多服务系统，或者有领域级 guardrails 的团队适合使用 domain 模式。

## 和其他工具的关系

| 工具 | 适合做什么 | NOC 的角色 |
|---|---|---|
| README | 项目概览和启动方式 | 在改动前把 agent 指向 feature 级项目记忆。 |
| Wiki 或文档站 | 长文指南和广泛知识 | 把和代码改动强相关的记忆放在代码工作流旁边。 |
| ADR | 架构决策 | 记录 feature 行为、限制、测试和变更事实。 |
| Issue tracker | 计划、负责人和讨论 | 保存实现后真正变成事实的内容。 |
| 自动生成 API 文档 | 从代码生成 reference | 捕获代码本身看不出来的意图、限制和验证。 |

NOC 可以和这些工具共存。它是本地路由层，告诉 agent 改代码前应该看哪里。

## 给 Coding Agents 使用

Codex 可以使用标准 skill 路径中的仓库内置 skill：

```text
.agents/skills/project-living-docs
```

项目内安装：

```bash
mkdir -p /path/to/project/.agents/skills
cp -R .agents/skills/project-living-docs /path/to/project/.agents/skills/
```

全局安装：

```bash
mkdir -p ~/.agents/skills
cp -R .agents/skills/project-living-docs ~/.agents/skills/
```

旧路径 `skills/codex/project-living-docs` 会保留以兼容已有用法；新 Codex 用户应复制 `.agents/skills/project-living-docs`。

通用 agent 可以读取 managed block：

```bash
noc init /path/to/project --agent-file AGENTS.md
```

细节见 [Agent Compatibility](docs/agent-compatibility.md)。

## 开发本仓库

```bash
python scripts/noc.py validate
python scripts/release.py --check
python -m unittest tests.test_noc_cli tests.test_release_cli
```

```bash
python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py
```

当前版本：`1.0.1`。

## GitHub 发现性

建议添加这些 GitHub topics：

```text
codex
codex-skill
agent-skills
ai-coding
agents-md
living-docs
developer-tools
documentation
cli
git-hooks
project-memory
```

更多阅读：

- [Why NOC](docs/why-noc.md)
- [Agent Compatibility](docs/agent-compatibility.md)
- [Comparisons](docs/comparisons.md)
- [v1 Readiness](docs/v1-readiness.md)
- [Migration Reports](docs/migration-reports/)

## 许可证

本仓库源码公开，默认用于非商业场景。

代码、脚本、模板和 skills 使用 PolyForm Noncommercial License 1.0.0。商业使用需要书面许可。

# NOC Living Docs

[![Validate](https://github.com/SmallNoc/noc-living-docs/actions/workflows/validate.yml/badge.svg)](https://github.com/SmallNoc/noc-living-docs/actions/workflows/validate.yml)
![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-yellow.svg)
![Codex Skill](https://img.shields.io/badge/Codex-Skill-blue)
![Living Docs](https://img.shields.io/badge/Living%20Docs-NOC-green)

A local project-memory Skill for Codex, with a CLI that handles setup and one-time project initialization.

## Start in three steps

### 1. Install

```bash
pipx install noc-living-docs
noc setup
```

### 2. Initialize a project once

```bash
cd my-project
noc init .
```

`noc init .` creates the default v2 simplified project memory. It does not create feature or domain documents.

### 3. Use Codex normally

```text
帮我给登录接口增加失败次数限制。
```

- You do not need to run `work`, `index`, `check`, `feature`, or `suggest-map` yourself.
- The Codex Skill automatically reads the smallest useful project memory.
- It updates memory only when a change creates a durable fact that future Codex sessions must know.
- Ordinary bug fixes and small refactors do not create documentation work.
- NOC does not call a model or upload code; all project memory stays in your project.

中文说明在下方：[中文](#中文)。

**License note:** you can read and use this for learning, research, and personal non-commercial work. Commercial use needs written permission.

## Advanced usage

The commands and protocol details below are optional. The Codex Skill runs the relevant commands automatically during normal development.

## Why NOC

AI coding agents are fast, but project memory is fragile. Requirements disappear with chat sessions, guardrails are forgotten, and verification knowledge is easily buried. NOC is a local agent memory router: it tells an agent which small set of durable project facts to read before changing code.

For a default v2 simplified project, the deterministic first step is:

```bash
noc work . --path src/app.py --json
```

## What It Looks Like

The following is the actual JSON shape returned for that path in a newly initialized v2 project:

```json
{
  "schema_version": "1.0",
  "protocol_version": 2,
  "layout": "simplified",
  "resolution_status": "project_memory",
  "intent": null,
  "paths": [
    "src/app.py"
  ],
  "features": [
    {
      "id": "project",
      "read_before_code": [
        "noc_docs/project.md",
        "noc_docs/guardrails.md",
        "noc_docs/verification.md"
      ],
      "before_coding": [],
      "update_after_code": [
        {
          "doc": "project memory",
          "reason": "only when future sessions need a new fact"
        }
      ]
    }
  ],
  "next_actions": [],
  "finish_commands": []
}
```

## Generated Documents

Default `noc init .` creates the v2 simplified structure:

```text
<project>/
  AGENTS.md
  noc_docs/
    project.md
    guardrails.md
    verification.md
    .living-docs/
      config.json
      routing.json
      manifest.json
```

The three Markdown files have distinct responsibilities:

| File | Purpose |
|---|---|
| `noc_docs/project.md` | Durable goals, phase, capabilities, boundaries, and architecture facts. |
| `noc_docs/guardrails.md` | Durable constraints involving security, compatibility, permissions, data loss, APIs, migration, or deployment. |
| `noc_docs/verification.md` | Standard test, build, release, and acceptance commands or gates. |

The `.living-docs` JSON files store protocol configuration, routing, and the generated file manifest. Agents use them through `noc work --json` rather than parsing them by hand.
The v2 routing file is `noc_docs/.living-docs/routing.json`.

## Default v2 workflow

Before changing code, run `noc work` and read the returned files. After changing code, classify whether the diff creates a durable project, guardrail, or verification fact. Update only the matching memory file; routine fixes and tests do not require a memory update. Then run the relevant checks:

```bash
noc doctor .
noc check . --staged --memory-impact none
```

Use `--memory-impact project`, `guardrails`, or `verification` when the diff creates that kind of durable fact. The Codex Skill handles this during normal use.

## Installation and updates

With `pip`:

```bash
python -m pip install noc-living-docs
noc setup
```

The package installs the `noc` CLI. `noc setup`, available since 1.1.0, installs the bundled, matching-version `project-living-docs` Skill into Codex. Run both once per machine. Upgrade with `pipx upgrade noc-living-docs` or `python -m pip install --upgrade noc-living-docs`, then run `noc setup` again.

For local development without installing:

```bash
git clone https://github.com/SmallNoc/noc-living-docs.git
cd noc-living-docs
python scripts/noc.py --help
```

## Command reference

| Command | What it does |
|---|---|
| `noc setup` | Installs or checks the matching Codex Skill. |
| `noc init <project>` | Creates default v2 simplified project memory and an agent entry block. |
| `noc doctor <project>` | Checks setup, JSON, Git, mode, indexes, and hook state. |
| `noc work <project> --path <path> --json` | Routes a path to the memory an agent should read. |
| `noc check <project>` | Verifies memory impact against changed files. |
| `noc index <project>` | Refreshes generated routing files. |
| `noc validate --target <project>` | Validates a target project. |
| `noc validate` | Validates this repository. |

Use `noc <command> --help` for arguments.

## Legacy v1 / Advanced compatibility

The v1 feature/domain protocol remains supported for existing projects and explicit compatibility use. It is not the default and is never created by plain `noc init .`.

- `noc init . --mode small` explicitly creates the v1 small feature layout.
- `noc init . --mode domain` explicitly creates the v1 domain layout.
- Existing v1 projects are not implicitly migrated by a later default init.
- `noc feature create`, `noc feature adopt`, `noc feature rename`, `noc suggest-map`, and `feature-map.json` are v1 advanced compatibility capabilities.

The v1 small layout keeps feature folders with `agent-guide.md`, `requirements.md`, `status.md`, `guardrails.md`, `test-record.md`, `change-record.md`, and `notes.md`. Domain mode nests the same feature model under domain-level indexes and guardrails. These documents and commands are intentionally retained, but they do not apply to v2 simplified projects.

## For Coding Agents

`noc setup` installs the bundled `project-living-docs` Skill into Codex's global Skill directory and keeps its version aligned with the CLI. The repository paths `.agents/skills/project-living-docs` and `skills/codex/project-living-docs` remain available for source development and compatibility.

Generic agents can read the managed block created by:

```bash
noc init /path/to/project --agent-file AGENTS.md
```

See [Agent Compatibility](docs/agent-compatibility.md) for the evidence-backed support matrix.

## Developing This Repo

```bash
python -m py_compile scripts/__init__.py scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py
python -m unittest discover -s tests
python scripts/noc.py validate
python scripts/release.py --check
```

Current version: `1.2.1`.

More reading: [Why NOC](docs/why-noc.md), [Agent Compatibility](docs/agent-compatibility.md), [Comparisons](docs/comparisons.md), and [Release](docs/release.md).

## License

This repo is source-available and non-commercial by default. Code, scripts, templates, and skills use the PolyForm Noncommercial License 1.0.0. Commercial use requires written permission.

---

## 中文

NOC 是 Codex 的本地项目记忆 Skill，CLI 负责安装和一次性项目初始化。

### 三步开始使用

1. 安装：

   ```bash
   pipx install noc-living-docs
   noc setup
   ```

2. 每个项目初始化一次：

   ```bash
   cd my-project
   noc init .
   ```

   `noc init .` 默认创建 v2 simplified 项目记忆，不会创建 feature 或 domain 文档。

3. 此后正常向 Codex 提出开发需求。无需手动运行 `work`、`index`、`check`、`feature` 或 `suggest-map`。

Codex Skill 会自动读取最小项目记忆，并且只在产生未来会话必须知道的新事实时更新记录。普通 Bug 修复和小型重构不会带来文档负担。NOC 不调用模型、不上传代码，所有记录都保存在项目本地。

## 高级用法

以下命令和协议细节均为可选内容；正常开发时由 Codex Skill 自动调用相关命令。

## 为什么需要 NOC

AI agent 写代码很快，但需求、限制和验证方式很容易随会话丢失。NOC 是本地 agent memory router，负责在改代码前把 agent 指向最小但足够的持久项目记忆。

默认 v2 simplified 项目的确定性入口是：

```bash
noc work . --path src/app.py --json
```

## 效果示例

新建 v2 项目对该路径返回的真实 JSON 结构如下：

```json
{
  "schema_version": "1.0",
  "protocol_version": 2,
  "layout": "simplified",
  "resolution_status": "project_memory",
  "intent": null,
  "paths": [
    "src/app.py"
  ],
  "features": [
    {
      "id": "project",
      "read_before_code": [
        "noc_docs/project.md",
        "noc_docs/guardrails.md",
        "noc_docs/verification.md"
      ],
      "before_coding": [],
      "update_after_code": [
        {
          "doc": "project memory",
          "reason": "only when future sessions need a new fact"
        }
      ]
    }
  ],
  "next_actions": [],
  "finish_commands": []
}
```

## 生成的文件

默认 `noc init .` 会创建 v2 simplified 结构：

```text
<project>/
  AGENTS.md
  noc_docs/
    project.md
    guardrails.md
    verification.md
    .living-docs/
      config.json
      routing.json
      manifest.json
```

`project.md` 保存目标、阶段、主要能力、边界和架构事实；`guardrails.md` 保存安全、兼容性、权限、数据丢失、API、迁移或部署限制；`verification.md` 保存标准测试、构建、发布和验收命令。`.living-docs` 下的 JSON 保存协议配置、路由和清单，agent 应通过 `noc work --json` 使用它们。
v2 路由文件的完整路径是 `noc_docs/.living-docs/routing.json`。

## 默认 v2 工作流

改代码前运行 `noc work` 并读取返回的文件。改完后判断 diff 是否产生持久的 project、guardrails 或 verification 事实，只更新对应文件；普通修复和普通测试无需更新项目记忆。最后执行对应检查：

```bash
noc doctor .
noc check . --staged --memory-impact none
```

如果产生对应的持久事实，使用 `--memory-impact project`、`guardrails` 或 `verification`。正常使用 Codex 时由 Skill 自动处理。

## 安装、更新和命令

也可以使用 `python -m pip install noc-living-docs` 安装，再运行 `noc setup`。使用 pipx 时通过 `pipx upgrade noc-living-docs` 更新；使用 pip 时通过 `python -m pip install --upgrade noc-living-docs` 更新，随后再次运行 `noc setup`。

主要命令包括 `noc setup`、`noc init`、`noc doctor`、`noc work --json`、`noc check`、`noc index` 和 `noc validate`。参数细节运行 `noc <command> --help`。

## Legacy v1 / 高级兼容

v1 feature/domain 协议继续支持已有项目和显式兼容场景，但不再是默认模式：

- `noc init . --mode small` 显式创建 v1 small feature 布局。
- `noc init . --mode domain` 显式创建 v1 domain 布局。
- 已有 v1 项目不会被后续默认 init 隐式迁移。
- `noc feature create`、`noc feature adopt`、`noc feature rename`、`noc suggest-map` 和 `feature-map.json` 都属于 v1 高级兼容能力。

v1 small 模式继续使用 feature 目录及 `agent-guide.md`、`requirements.md`、`status.md`、`guardrails.md`、`test-record.md`、`change-record.md`、`notes.md`；domain 模式在 domain 索引和 guardrails 下嵌套相同的 feature 模型。这些能力不会删除，但不适用于 v2 simplified 项目。

## 给 Coding Agents 使用

`noc setup` 会安装与 CLI 同版本的 Codex Skill。仓库中的 `.agents/skills/project-living-docs` 和 `skills/codex/project-living-docs` 用于源码开发和兼容。通用 agent 可读取 `noc init /path/to/project --agent-file AGENTS.md` 创建的 managed block。支持范围见 [Agent Compatibility](docs/agent-compatibility.md)。

## 开发本仓库

```bash
python -m py_compile scripts/__init__.py scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py
python -m unittest discover -s tests
python scripts/noc.py validate
python scripts/release.py --check
```

当前版本：`1.2.1`。

## 许可证

本仓库源码公开，默认用于非商业场景。代码、脚本、模板和 skills 使用 PolyForm Noncommercial License 1.0.0，商业使用需要书面许可。

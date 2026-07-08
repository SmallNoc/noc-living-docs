# NOC Living Docs

![CI](https://github.com/SmallNoc/noc-living-docs/actions/workflows/ci.yml/badge.svg)
![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-yellow.svg)
![Codex Skill](https://img.shields.io/badge/Codex-Skill-blue)
![Living Docs](https://img.shields.io/badge/Living%20Docs-NOC-green)

NOC is an **agent memory router** for codebases.

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

## Quick Start

Install:

```bash
pipx install noc-living-docs
noc --help
```

Or run from a checkout:

```bash
git clone https://github.com/SmallNoc/noc-living-docs.git
cd noc-living-docs
python scripts/noc.py --help
```

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

## How It Compares

| Tool | Good for | NOC's role |
|---|---|---|
| README | Project overview and setup | Points agents to feature-level memory before a change. |
| Wiki or docs site | Long-form guides and broad knowledge | Keeps change-critical memory next to the code workflow. |
| ADRs | Architectural decisions | Records feature behavior, guardrails, tests, and change facts. |
| Issue tracker | Planning, ownership, and discussion | Preserves what became true after implementation. |
| Generated API docs | Reference generated from code | Captures intent, constraints, and verification that code alone does not show. |

NOC can coexist with all of these. It is the local routing layer that tells an agent where to look before it edits code.

## Commands

| Command | What it does |
|---|---|
| `noc init` | Adds `noc_docs/` and an agent entry block. |
| `noc work` | Routes a feature, path, or Git diff to the docs an agent should read and update. Use `--json` for automation. |
| `noc check` | Warns or fails when code changed without matching NOC docs. |
| `noc index` | Refreshes generated `.living-docs` routing files. |
| `noc doctor` | Checks setup, JSON, Git, mode, indexes, and hook state. |
| `noc suggest-map` | Suggests code-path to feature mappings. |
| `noc feature create` | Creates a feature doc folder from the template. |
| `noc feature adopt` | Turns a placeholder feature folder into a real one. |
| `noc feature rename` | Renames a feature folder and its mapping. |
| `noc hook` | Installs, checks, or removes the pre-commit reminder. |
| `noc validate` | Validates this repo or a target project. |

Use `noc <command> --help` for arguments.

## Folder Shape

Small projects use:

```text
noc_docs/
  docs-map.md
  project-status.md
  development/
  features/
    <feature>/
      agent-guide.md
      requirements.md
      status.md
      guardrails.md
      test-record.md
      change-record.md
      notes.md
  .living-docs/
    feature-map.json
    docs-index.json
    manifest.json
    config.json
```

Feature docs are stable homes for project memory. They are not a checklist that must all change on every task.

Bigger projects can use domain mode:

```text
noc_docs/
  domains/
    <domain>/
      guardrails.md
      features/
        <feature>/
```

Domain mode is useful for monorepos, multi-service systems, or teams with domain-level guardrails.

## For Coding Agents

Codex can use the bundled skill:

```text
skills/codex/project-living-docs
```

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

Current version: `1.0.0`.

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

NOC 是给代码仓库用的 **agent memory router**。

它不想变成文档平台，而是给 AI 编程助手一个稳定的第一步：改代码前先知道该读哪里，改完后只把重要事实写回去。

## 为什么需要

AI agent 写代码很快，但项目记忆很容易丢：

- 需求留在聊天里。
- 当前行为藏在代码或旧 PR 里。
- guardrails 被新会话忘掉。
- 测试命令和缺口没有沉淀。
- agent 读太多、读错文件，或者自信地猜错。

NOC 把代码路径映射到功能记忆：

```bash
noc work . --path src/auth/login.py --json
```

它会告诉 agent：命中了哪个 feature、置信度如何、改代码前读哪些文档、改完后哪些事实可能需要更新。

## 最小流程

给项目接入：

```bash
noc init /path/to/project
noc doctor /path/to/project
```

创建 feature 并映射代码路径：

```bash
noc feature create /path/to/project user-login --path src/auth/
```

改代码前：

```bash
noc work /path/to/project --path src/auth/login.py --json
noc work /path/to/project --staged --json
noc work /path/to/project --changed --json
```

agent 只读 work plan 里列出的文档。改完后，只更新真的变化了的事实：

- 目标行为变了，更新 `requirements.md`。
- 当前行为变了，更新 `status.md`。
- 验证做了或有缺口，更新 `test-record.md`。
- 有以后值得记住的实现变化，更新 `change-record.md`。

最后：

```bash
noc index /path/to/project
noc check /path/to/project --staged
```

一句话：NOC 不是让项目写更多文档，而是让 agent 少误判、少乱读、少忘记约束。

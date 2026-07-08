# NOC Living Docs

![CI](https://github.com/SmallNoc/noc-living-docs/actions/workflows/ci.yml/badge.svg)
![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-yellow.svg)
![Codex Skill](https://img.shields.io/badge/Codex-Skill-blue)
![Living Docs](https://img.shields.io/badge/Living%20Docs-NOC-green)

NOC is an agent memory router for codebases.

It gives AI coding agents one reliable way to answer four questions before and after a change:

- Which feature or domain am I touching?
- What is the smallest set of project memory I should read?
- Which guardrails must not be broken?
- What facts changed enough to update living docs?

NOC is not a wiki, issue tracker, ADR system, release platform, dashboard, or model runtime. The CLI does not call a model. It routes agents to the right local project memory and checks for code/docs drift.

中文说明在下方：[中文](#中文)。

**License note:** you can read and use this for learning, research, and personal non-commercial work. Commercial use needs written permission.

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

Create docs for a feature:

```bash
noc feature create /path/to/project user-login --path src/auth/
```

Before changing code, ask NOC where the agent should look:

```bash
noc work /path/to/project --path src/auth/login.py --json
noc work /path/to/project --staged --json
noc work /path/to/project --changed --json
```

After changing code, update only the facts that changed, then verify:

```bash
noc index /path/to/project
noc check /path/to/project --staged
```

## Agent Loop

1. Run `noc work <project> --path <code/path> --json`, or use `--staged` / `--changed`.
2. Read only the docs listed in the work plan.
3. Update `requirements.md` only when intended behavior changes.
4. Update `status.md` when actual behavior changes.
5. Update `test-record.md` with verification commands and results.
6. Update `change-record.md` only for changes worth remembering.
7. Run `noc index` and `noc check --staged`.

For Codex, use the skill at:

```text
skills/codex/project-living-docs
```

For a generic agent entry file:

```bash
noc init /path/to/project --agent-file AGENTS.md
```

## Commands

| Command | What it does |
|---|---|
| `noc init` | Adds `noc_docs/` and an agent entry block. |
| `noc work` | Routes a feature/path/Git diff to the docs an agent should read and update. Use `--json` for automation. |
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

The feature files are a stable home for project memory. They are not a checklist that must all change every time. Most code changes only need `status.md`, `test-record.md`, or no docs update at all.

Bigger projects can use domain mode:

```text
noc_docs/
  domains/
    <domain>/
      guardrails.md
      features/
        <feature>/
```

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

- [Agent Compatibility](docs/agent-compatibility.md)
- [Why NOC](docs/why-noc.md)
- [Comparisons](docs/comparisons.md)
- [v1 Readiness](docs/v1-readiness.md)
- [Migration Reports](docs/migration-reports/)

## License

This repo is source-available and non-commercial by default.

Code, scripts, templates, and skills are licensed under the PolyForm Noncommercial License 1.0.0. For commercial use, get written permission first.

---

## 中文

NOC 是给代码仓库用的 agent memory router：它不想变成文档平台，只负责把 AI 编程助手带到正确的项目记忆位置。

它帮 agent 在改代码前后回答四个问题：

- 这次碰的是哪个功能或领域？
- 最少应该读哪些项目记忆？
- 哪些限制不能破坏？
- 哪些事实变化值得写回活文档？

NOC 不替代 Wiki、issue、ADR、发布平台、仪表盘或模型调用。CLI 本身不调用模型。

## 最小流程

给项目接入：

```bash
noc init /path/to/project
noc doctor /path/to/project
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

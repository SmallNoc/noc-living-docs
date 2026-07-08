# NOC Living Docs

![CI](https://github.com/SmallNoc/noc-living-docs/actions/workflows/ci.yml/badge.svg)
![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-yellow.svg)
![Codex Skill](https://img.shields.io/badge/Codex-Skill-blue)
![Living Docs](https://img.shields.io/badge/Living%20Docs-NOC-green)

NOC keeps the notes around your code from wandering off.

It gives a project one folder, `noc_docs/`, for the things people keep having to rediscover: what a feature is meant to do, what the code does today, what must not break, how it was tested, and why the last real change happened.

中文说明在下方：[中文](#中文)。

**License note:** you can read and use this for learning, research, and personal non-commercial work. Commercial use needs written permission.

## Why It Exists

Most projects do not fail because nobody wrote docs. They fail because the useful bits are scattered:

- a requirement in a chat thread
- a warning in an old PR
- a test command in someone's terminal history
- a behavior note that only lives in one person's head

That gets even messier with AI coding agents. They can read files, but they still need a good starting point.

NOC is a small CLI and folder convention for that job. It does not try to become your Wiki, issue tracker, ADR system, or API reference. It just keeps feature notes close to the code they describe.

More on the boundary: [NOC Living Docs and adjacent tools](docs/comparisons.md).

## What It Adds

- A `noc_docs/` folder with a clear shape.
- Feature docs for requirements, current status, guardrails, tests, changes, and notes.
- A `feature-map.json` that maps code paths to feature docs.
- A local CLI for setup, indexing, checks, and day-to-day work plans.
- Agent entry files for `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`.
- A Codex skill at `skills/codex/project-living-docs`.
- A pre-commit hook option that warns when code changed but related docs did not.
- The CLI itself does not call a model.

## Start Here

| If you are... | Start with... |
|---|---|
| Adding NOC to a project | `noc init <project>` then `noc doctor <project>` |
| Asking an agent to change code | `noc work <project> --path <code/path> --json` |
| Maintaining this repo | `python scripts/noc.py work . --path <path> --json` |
| Checking before commit | `noc check <project> --staged --warn-only` |

## Install

```bash
pipx install noc-living-docs
noc --help
```

You can also install it with pip:

```bash
python -m pip install noc-living-docs
```

Or run it from a checkout:

```bash
git clone https://github.com/SmallNoc/noc-living-docs.git
cd noc-living-docs
python scripts/noc.py --help
```

## Quick Start

Add NOC to a project:

```bash
noc init /path/to/project
noc doctor /path/to/project
noc validate --target /path/to/project
```

Create docs for a real feature:

```bash
noc feature create /path/to/project user-login --path src/auth/
```

Before a change, ask what to read:

```bash
noc work /path/to/project --feature user-login --intent "lock the account after 5 failed login attempts"
noc work /path/to/project --path src/auth/login.py --json
```

After code and docs are updated:

```bash
noc index /path/to/project
noc check /path/to/project --staged
```

## Working With Coding Agents

The usual loop is:

1. Run `noc work` for the feature or path you are touching. Agents should prefer `--json` for machine-readable output.
2. Read the docs it lists.
3. Put agreed intent in `requirements.md`.
4. Put what the code actually does in `status.md`.
5. Put test commands and results in `test-record.md`.
6. Put changes worth remembering in `change-record.md`.
7. Run `noc index` and `noc check --staged`.

For Codex, use:

```text
skills/codex/project-living-docs
```

For a generic agent entry file:

```bash
noc init /path/to/project --agent-file AGENTS.md
```

See [Agent Compatibility](docs/agent-compatibility.md) for the details.

## Commands

| Command | What it does |
|---|---|
| `noc init` | Adds `noc_docs/` and an agent entry block. |
| `noc doctor` | Checks setup, indexes, JSON, Git, mode, and hook state. |
| `noc validate` | Validates this repo or a target project. |
| `noc index` | Refreshes the generated `.living-docs` files. |
| `noc work` | Prints the docs to read before coding and update after coding. Use `--json` for agents and automation. |
| `noc check` | Warns or fails when code changed without matching NOC docs. |
| `noc hook` | Installs, checks, or removes the pre-commit reminder. |
| `noc suggest-map` | Suggests code-path to feature mappings. |
| `noc feature create` | Creates a feature doc folder from the template. |
| `noc feature adopt` | Turns a placeholder feature folder into a real one. |
| `noc feature rename` | Renames a feature folder and its mapping. |

Use `noc <command> --help` when you need details.

## Folder Shape

Small projects get this:

```text
noc_docs/
  docs-map.md
  project-status.md
  development/
    git-workflow.md
    testing.md
    documentation-policy.md
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
    config.json
    manifest.json
    feature-map.json
    docs-index.json
```

Bigger projects can use domain mode:

```text
noc_docs/
  domains/
    <domain>/
      guardrails.md
      features/
        <feature>/
          agent-guide.md
          requirements.md
          status.md
          guardrails.md
          test-record.md
          change-record.md
          notes.md
```

Domain mode is useful for monorepos, multi-service projects, larger feature sets, or teams with domain-level rules.

## What Goes Where

| File | Put this there |
|---|---|
| `agent-guide.md` | The quick entry point for this feature. |
| `requirements.md` | What the feature is supposed to do. |
| `status.md` | What the code does right now. |
| `guardrails.md` | Things that must not break. |
| `test-record.md` | Test strategy, commands, results, and gaps. |
| `change-record.md` | Changes worth remembering later. |
| `notes.md` | Scratch notes, questions, and temporary findings. |

One rule matters most: do not rewrite `requirements.md` just to match current code. If the code does something different, say so in `status.md`, then decide whether the code or the requirement should change.

## Developing This Repo

```bash
python scripts/noc.py validate
python scripts/release.py --check
python -m unittest tests.test_noc_cli tests.test_release_cli
```

```bash
python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py
```

Release bookkeeping uses `VERSION`, `CHANGELOG.md`, and tags like `v1.0.0`.

## Status

Current version: `1.0.0`.

This release covers the main loop: create the docs, map paths to features, point agents at the right files, check for code/docs drift, and keep the Codex skill lined up with the protocol.

More reading:

- [v1 Readiness](docs/v1-readiness.md)
- [Agent Compatibility](docs/agent-compatibility.md)
- [Why NOC](docs/why-noc.md)
- [Comparisons](docs/comparisons.md)
- [Migration Reports](docs/migration-reports/)

## License

This repo is source-available and non-commercial by default.

Code, scripts, templates, and skills are licensed under the PolyForm Noncommercial License 1.0.0. For commercial use, get written permission first.

---

## 中文

NOC 做的事很简单：让代码旁边那点有用的项目记忆，别越走越远。

它会在项目里放一个固定的 `noc_docs/` 目录，用来写那些大家总是反复追问的东西：这个功能本来要做什么，现在代码实际怎么做，有哪些不能碰的限制，怎么测过，上次重要修改为什么这么改。

**许可说明：**本仓库源码公开，允许学习、研究和个人非商业使用。商业使用需要作者书面许可。

## 为什么要有它

很多项目不是没有文档，而是有用的信息散得到处都是：

- 需求在聊天记录里
- 风险提醒在某个旧 PR 里
- 测试命令在某个人的终端历史里
- 当前行为只有维护者自己记得

这对 AI 编程助手也很麻烦。它们会读文件，但前提是得知道先读哪几个文件。

NOC 就是为这件事做的一个小 CLI 和目录约定。它不想替代 Wiki、issue、ADR、README 或自动生成的 API 文档，只负责把和代码修改强相关的 feature 记忆放稳。

边界说明见：[NOC Living Docs 和相邻工具的边界](docs/comparisons.md)。

## 它会加什么

- 一个结构固定的 `noc_docs/` 目录。
- 每个功能自己的需求、现状、限制、测试、变更和笔记。
- 一个把代码路径映射到功能文档的 `feature-map.json`。
- 用来初始化、索引、检查和生成工作清单的本地命令。
- `AGENTS.md`、`CLAUDE.md`、`GEMINI.md` 入口模板。
- `skills/codex/project-living-docs` 里的 Codex skill。
- 可选的 pre-commit hook，用来提醒“代码改了，相关文档是不是也该改”。
- CLI 本身不调用模型。

## 从这里开始

| 如果你是... | 先运行... |
|---|---|
| 给项目接入 NOC | `noc init <project>`，然后 `noc doctor <project>` |
| 让 agent 改代码 | `noc work <project> --path <code/path> --json` |
| 维护本仓库 | `python scripts/noc.py work . --path <path> --json` |
| 提交前检查 | `noc check <project> --staged --warn-only` |

## 安装

```bash
pipx install noc-living-docs
noc --help
```

也可以用 pip：

```bash
python -m pip install noc-living-docs
```

源码方式：

```bash
git clone https://github.com/SmallNoc/noc-living-docs.git
cd noc-living-docs
python scripts/noc.py --help
```

## 快速开始

给项目接入 NOC：

```bash
noc init /path/to/project
noc doctor /path/to/project
noc validate --target /path/to/project
```

给真实功能创建文档：

```bash
noc feature create /path/to/project user-login --path src/auth/
```

改代码前，先问这次该读哪些文档：

```bash
noc work /path/to/project --feature user-login --intent "登录失败 5 次后锁定账号"
noc work /path/to/project --path src/auth/login.py --json
```

代码和文档都改完后：

```bash
noc index /path/to/project
noc check /path/to/project --staged
```

## 和编程助手一起用

日常就是这个循环：

1. 用 `noc work` 指定要改的功能或路径。agent 和自动化场景优先用 `--json`。
2. 只读它列出来的文档。
3. 已确认的目标行为写进 `requirements.md`。
4. 当前代码实际行为写进 `status.md`。
5. 测试命令和结果写进 `test-record.md`。
6. 值得以后记住的实现变化写进 `change-record.md`。
7. 最后跑 `noc index` 和 `noc check --staged`。

Codex 可以用：

```text
skills/codex/project-living-docs
```

通用 agent 入口：

```bash
noc init /path/to/project --agent-file AGENTS.md
```

细节见：[Agent Compatibility](docs/agent-compatibility.md)。

## 常用命令

| 命令 | 做什么 |
|---|---|
| `noc init` | 添加 `noc_docs/` 和 agent 入口区块。 |
| `noc doctor` | 检查环境、索引、JSON、Git、目录模式和 hook。 |
| `noc validate` | 校验本仓库或目标项目。 |
| `noc index` | 刷新 `.living-docs` 里的生成信息。 |
| `noc work` | 输出改代码前要读、改完后要更新的文档；agent 和自动化可用 `--json`。 |
| `noc check` | 检查代码变更有没有对应的 NOC 文档变更。 |
| `noc hook` | 安装、查看或移除 pre-commit 提醒。 |
| `noc suggest-map` | 建议代码路径到功能文档的映射。 |
| `noc feature create` | 从模板创建功能文档目录。 |
| `noc feature adopt` | 把占位功能目录转成真实功能目录。 |
| `noc feature rename` | 重命名功能目录和映射。 |

想看参数就跑 `noc <command> --help`。

## 目录长什么样

小项目默认是这样：

```text
noc_docs/
  docs-map.md
  project-status.md
  development/
    git-workflow.md
    testing.md
    documentation-policy.md
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
    config.json
    manifest.json
    feature-map.json
    docs-index.json
```

大一点的项目可以用 domain mode：

```text
noc_docs/
  domains/
    <domain>/
      guardrails.md
      features/
        <feature>/
          agent-guide.md
          requirements.md
          status.md
          guardrails.md
          test-record.md
          change-record.md
          notes.md
```

monorepo、多服务项目、功能很多的项目，或者有业务域级别限制的项目，更适合 domain mode。

## 每个文件放什么

| 文件 | 放什么 |
|---|---|
| `agent-guide.md` | 这个功能的快速入口。 |
| `requirements.md` | 功能应该是什么样。 |
| `status.md` | 代码现在实际是什么样。 |
| `guardrails.md` | 不能破坏的限制。 |
| `test-record.md` | 测试策略、命令、结果和缺口。 |
| `change-record.md` | 以后值得回头看的变更。 |
| `notes.md` | 草稿、问题、临时结论。 |

最重要的一条：不要为了迁就当前代码，偷偷把 `requirements.md` 改成现状。如果代码和需求不一致，先把现状写进 `status.md`，再决定是改代码还是改需求。

## 开发这个仓库

```bash
python scripts/noc.py validate
python scripts/release.py --check
python -m unittest tests.test_noc_cli tests.test_release_cli
```

```bash
python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py
```

发布相关信息看 `VERSION`、`CHANGELOG.md` 和 `v1.0.0` 这类 tag。

## 当前状态

当前版本：`1.0.0`。

这个版本覆盖主流程：初始化文档、把路径映射到功能、让 agent 读对文档、检查代码和文档有没有脱节，并维护一份跟协议同步的 Codex skill。

更多文档：

- [v1 Readiness](docs/v1-readiness.md)
- [Agent Compatibility](docs/agent-compatibility.md)
- [Why NOC](docs/why-noc.md)
- [Comparisons](docs/comparisons.md)
- [Migration Reports](docs/migration-reports/)

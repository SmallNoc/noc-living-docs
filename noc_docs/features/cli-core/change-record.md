# Change Record: cli-core

## 2026-07-16 - structured feature update command

- Reason: implement stage 4 so future Skill workflows submit structured facts while the CLI owns safe, local, idempotent `overview.md` writes.
- Changed: added `noc feature update --id --patch-file --json`; added structured patch validation, stable `noc:id` Markdown markers, localized section updates, SHA conflict checks, backup creation, atomic writes, and derived index refresh after real changes.
- Compatibility: command is restricted to feature-archive layout; simplified, small, and domain projects are not migrated or modified.
- Verification: stage 4 update tests, full unittest discovery, repository validation, release check, and wheel-isolated update verification passed.

## 2026-07-16 - feature-archive candidate routing and ensure

- Reason: implement stage 3 of the MVP without adding structured updates, evidence recording, migration, or Skill automation.
- Changed: `work --json` now scores feature-archive candidates with deterministic evidence from ids, names, aliases, overview text, code paths, and status; `noc feature ensure` creates a missing feature overview idempotently with Chinese body text when the project language is `zh-CN`.
- Compatibility: `work` remains read-only, falls back to overview scanning when the feature index is missing, and does not modify old simplified projects.
- Verification: targeted routing and ensure tests, full unittest discovery, repository validation, release check, stage 3 no-write checks, and isolated wheel ensure/index/work verification passed.

## 2026-07-16 - feature-archive stage 1 CLI recognition

- Reason: implement the first MVP stage for schema and read-only layout recognition without changing new-project init defaults.
- Changed: added `scripts.noclib.schemas` and `scripts.noclib.layouts`; updated `doctor` to recognize feature-archive projects and report language configuration; allowed `noc validate <target>` as a positional equivalent of `--target`.
- Compatibility: existing v2 simplified projects remain read-only under `work`, `index`, `doctor`, and `validate`; v1 small/domain routing remains unchanged.
- Verification: `python -m unittest discover -s tests`, `python scripts/noc.py validate .`, `python scripts/release.py --check`, and the explicit simplified no-write hash comparison passed.

## 2026-07-16 - feature-archive project-memory routing

- Reason: after new init creates feature-archive projects, existing `work` and semantic memory-impact checks must still return the v2 project-memory contract.
- Changed: `work --json` recognizes `layout: feature-archive` and returns project-level memory plus `layout_version`; `check --memory-impact` treats feature-archive project-level memory files like simplified v2 for project/guardrails/verification impacts.
- Non-goals: no candidate routing, feature ensure, structured update, evidence record, or migration command was added.
- Verification: full unittest discovery and stage 2 targeted tests passed.

## 2026-07-14 - Add declarative semantic memory checks

- Added repeatable `--memory-impact` categories and machine-readable check output.
- Made `none` pass without documentation changes and durable impacts require only their corresponding project memory.
- Kept semantic judgment in the Skill; the CLI only verifies the declared impact against the Git diff.

## 2026-07-14 - Route simplified project memory

- Added protocol/layout fields to work-plan JSON without removing v1 fields.
- Added v2 project-level fallback context and non-mandatory documentation checks.
- Kept all v1 commands and explicit legacy initialization modes available.

## 2026-07-13 - Add the Codex Skill setup lifecycle

- Added `noc setup`, `--check`, `--repair`, and `--json`.
- Setup installs missing or outdated NOC-managed Skills idempotently and refuses to overwrite user-managed collisions.
- Added explicit CLI/Skill version matching and actionable next-step output.
- Release review strengthened managed identity validation, stable JSON error codes, interrupted-write recovery, and reserved-path collision handling.

## 2026-07-08 - Add machine-readable work plans

### Reason

Codex 和其他 agent 需要稳定读取“该读哪些文档、该更新哪些文档、最后跑哪些命令”，自由文本不适合作为自动化接口。

### Changed

- `noc work` 增加 `--json`。
- 抽出 work plan 构建逻辑，让文本输出和 JSON 输出共用同一份数据。
- 增加 unittest 覆盖 JSON 输出和旧文本输出兼容性。

### Impact

- agent 可以直接解析 work plan。
- 人类默认使用方式不变。

## 2026-07-08 - Tighten work plan routing contract

### Reason

NOC 的核心目标是作为 agent memory router，而不是让 agent 自己猜路径、解析自由文本或在低置信度场景继续误判。

### Changed

- `work --json` 增加 `schema_version`、`resolution_status`、匹配原因、匹配路径、匹配 pattern 和置信度。
- missing feature 和 unresolved path 会返回明确状态和 `next_actions`。
- `work` 增加 `--changed` 和 `--staged`，可直接从 Git diff 收集路径。

### Impact

- agent 可以区分 resolved、unresolved 和 missing feature。
- 常见工作流可以直接用 Git diff 路由，不需要 agent 自己拼 `--path` 参数。

## 2026-07-14 - Finalize zero-learning CLI entry points

### Changed

- Added `noc --version` using the existing formal version source.
- Reordered the top-level help experience around setup and initialization, with existing maintenance commands clearly marked Advanced.

### Impact

- New users can verify the installed version and discover the normal Codex workflow without learning internal commands.

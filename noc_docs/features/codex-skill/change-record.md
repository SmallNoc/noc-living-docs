# Change Record: codex-skill

## 2026-07-17 - Add feature-archive zero-learning workflow

- Added the complete feature-archive Skill loop around `noc work`, `noc feature ensure`, `noc feature update`, `noc evidence`, `noc evidence record`, and `noc check --feature-impact-file`.
- Added safety limits for `overview.md` updates, confirmed requirements, passed verification, major-change classification, feature creation, and old-layout migration.
- Added zh-CN language rules and eval prompts, then mirrored the same runtime content under both maintained Skill trees.

## 2026-07-14 - Separate v2 and v1 completion rules

- Split Definition of Done into v2 simplified and v1 legacy sections in both maintained Skill trees.
- Kept the runtime content synchronized and added a regression assertion that v2 does not require v1 document types.
- Removed obsolete workflow-mode guidance from both synchronized runtime references.

## 2026-07-13 - Bundle and install the Skill with the CLI

- Added the NOC-managed Skill version manifest.
- Packaged the standard Skill and runtime references into the wheel.
- Replaced repository-local `python scripts/noc.py` calls with installed `noc` commands in both maintained Skill paths.
- Added full runtime-content parity testing for the standard and compatibility Skill trees.

## 2026-07-09 - Add standard Codex skill path

### Reason

Codex users need a standard `.agents/skills/project-living-docs/` directory they can copy into a project or global skill folder without guessing from the legacy repo layout.

### Changed

- Added `.agents/skills/project-living-docs/` with the same `SKILL.md`, references, and evals as the legacy `skills/codex/project-living-docs/` path.
- Updated the skill description to front-load AI-assisted code change and living docs synchronization trigger keywords.
- Added regression coverage for both skill paths.

### Impact

- New Codex users can copy the standard skill path while existing users of `skills/codex/project-living-docs/` remain compatible.

## 2026-07-08 - Prefer machine-readable work plans

### Reason

Codex 使用结构化 work plan 比解析自由文本更稳定，能更容易定位需要读取和更新的 NOC 文档。

### Changed

- Codex skill 的执行步骤改为优先运行 `work ... --json`。
- 明确 JSON 不可用时才 fallback 到文本输出。

### Impact

- Codex 和 CLI 的 agent-first 路由方式保持一致。


# Change Record: init-index-validate

## 2026-07-16 - feature-archive migration rebuilds

- Reason: stage 6 migrations must produce valid feature-archive projects without treating derived JSON as source of truth.
- Changed: simplified migration updates config and rebuilds derived indexes; v1 migration creates feature overview files plus `legacy/` copies of original v1 Markdown, preserving domain metadata when present.
- Compatibility: ordinary init/index/validate/doctor/work/check/evidence paths still do not migrate old simplified or v1 projects.
- Verification: migration tests cover dry-run zero-write, apply backup, rollback, v1 original text preservation, conflict refusal, unsafe path refusal, and post-apply validate for v1 migration.

## 2026-07-16 - evidence index rebuild

- Reason: stage 5 evidence files must have a rebuildable derived index without making index a command runner.
- Changed: `noc index` rebuilds `evidence-index.json` from stored evidence JSON files and reports damaged evidence files as errors.
- Compatibility: Markdown facts are not changed by evidence index rebuild; old simplified/small/domain index behavior remains compatible.
- Verification: evidence index deletion/rebuild tests, damaged evidence test, full unittest discovery, and stage 5专项脚本 passed.

## 2026-07-16 - simplified initializer hash regression

- Reason: stage 3.1 fixed a reported regression in the direct simplified initializer path.
- Changed: restored the `hashlib` import used to build SHA-256 manifest entries in `scripts/init-noc-docs.py --layout simplified`.
- Compatibility: no init layout behavior changed; feature-archive default init remains unchanged.
- Verification: the new direct simplified initializer regression test failed with `NameError: hashlib is not defined` before the fix and passed after the import was restored.

## 2026-07-16 - feature update index and backup behavior

- Reason: stage 4 structured overview updates must keep derived indexes rebuildable while preserving rollback evidence.
- Changed: successful `feature update` writes a timestamped backup, atomically replaces overview, and rebuilds feature-archive derived indexes only when content changes.
- Compatibility: unchanged, invalid, conflict, and unsupported-layout results do not create backups or modify derived indexes.
- Verification: stage 4 update tests and专项脚本 covered backup equality, unchanged idempotency, SHA conflict zero-write, and wheel-installed update.

## 2026-07-16 - feature ensure index integration

- Reason: stage 3 feature creation must leave rebuildable derived indexes consistent without making `work` a writer.
- Changed: `noc feature ensure` creates a feature overview and then rewrites feature-archive derived indexes through the existing index builder; `work` can still route from overview files if `feature-index.json` is absent.
- Compatibility: `work` fallback remains read-only and old simplified projects are not converted or repaired by ordinary commands.
- Verification: stage 3 targeted tests and the explicit missing-index fallback/no-write script passed.

## 2026-07-16 - read-only feature-archive validation

- Reason: establish schema and layout recognition before implementing creation, routing, updates, evidence, or migration.
- Changed: `validate-noc-docs.py` accepts feature-archive projects, validates overview frontmatter, reports language configuration, and remains read-only. `noc validate <target>` now forwards to the same target validation path as `--target`.
- Compatibility: simplified projects without `language` remain valid and are reported as `unspecified`; no ordinary validation or doctor path mutates existing simplified projects.
- Verification: targeted stage 1 tests, full unittest discovery, repository validation, release check, and explicit old simplified no-write regression passed.

## 2026-07-16 - feature-archive init and rebuildable indexes

- Reason: implement stage 2 of the MVP: new init and deterministic, rebuildable indexes.
- Changed: new default `noc init` creates feature-archive layout with Chinese project-level Markdown, empty `features/`, feature-archive config, and four derived JSON files. `noc index` rebuilds feature-archive routing, manifest, feature index, and evidence index from Markdown facts.
- Compatibility: existing v2 simplified projects are not converted by default init or ordinary commands; v1 small/domain explicit modes remain available.
- Verification: stage 2 init/index tests, simplified compatibility tests, full unittest discovery, repository validation, release check, old simplified no-write script, and isolated wheel init/index verification passed.

## 2026-07-14 - Add simplified protocol v2 initialization

- Made bare `noc init <project>` create only project, guardrails, verification, routing, config, manifest, and the managed AGENTS block.
- Added safe project-file detection, idempotent writes, internal indexing, and v2 validation/doctor support.
- Preserved explicit legacy modes and existing v1 projects without migration or deletion.

## 2026-07-10 - Validate PyPI release files

### Reason

PyPI publishing support adds release documentation and a tag-triggered workflow that should be part of repository self-validation.

### Changed

- Added `docs/release.md` and `.github/workflows/publish.yml` to required repository paths in `validate-noc-docs.py`.

### Impact

- `python scripts/noc.py validate` fails if release documentation or the PyPI publish workflow is accidentally removed.

## 2026-07-09 - Validate standard Codex skill path

### Reason

The repository self-check still assumed the legacy skill path and a `Use when` description prefix, while the recommended Codex skill description now starts with `Use for` and the standard install path is `.agents/skills/project-living-docs/`.

### Changed

- Added `.agents/skills/project-living-docs/` files to repository validation.
- Updated skill frontmatter validation to accept descriptions starting with either `Use when` or `Use for`.

### Impact

- `python scripts/noc.py validate` remains compatible with the old path while enforcing that the new standard skill path is present.

## 2026-07-08 - Dogfood NOC in this repository

### Reason

The NOC project itself should be the best example of how to structure living docs for agents and maintainers.

### Changed

- Initialized `AGENTS.md` and `noc_docs/` in the main repository.
- Created five real feature doc folders and mapped core source paths.

### Impact

- `noc doctor .` and `noc work . --path <path>` can now operate against this repository's own NOC docs.


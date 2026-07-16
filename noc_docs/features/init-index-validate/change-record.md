# Change Record: init-index-validate

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


# Change Record: init-index-validate

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


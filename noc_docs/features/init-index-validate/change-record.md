# Change Record: init-index-validate

## 2026-07-08 - Dogfood NOC in this repository

### Reason

The NOC project itself should be the best example of how to structure living docs for agents and maintainers.

### Changed

- Initialized `AGENTS.md` and `noc_docs/` in the main repository.
- Created five real feature doc folders and mapped core source paths.

### Impact

- `noc doctor .` and `noc work . --path <path>` can now operate against this repository's own NOC docs.


# Migration Report: noc-living-docs

Date: 2026-07-04

## Project

- Repository: `SmallNoc/noc-living-docs`
- Stack: Python CLI, Markdown protocol/templates, GitHub Actions
- Shape: small CLI/tooling repository
- Existing docs: `docs/migration-reports/`
- Existing agent files: none in the temporary dogfood copy before initialization

## Commands

Executed against a temporary copy of this repository:

```bash
python scripts/noc.py init <temp-copy> --mode auto
python scripts/noc.py validate --target <temp-copy>
python scripts/noc.py index <temp-copy>
python scripts/noc.py suggest-map <temp-copy>
python scripts/noc.py check <temp-copy> --staged --warn-only
```

## Results

- Selected mode: `small`
- Created files: 17
- Updated files: `AGENTS.md`, `noc_docs/`
- Preserved files: existing `docs/` was left untouched
- Validation: passed with expected warning that `docs/` exists while NOC uses `noc_docs/`
- Index: generated 13 indexed documents
- Suggest map: no suggestions, expected because the repo has no `src/`, `apps/`, `services/`, `modules/`, or `domains/` code tree
- Check: detected staged SQL and Dockerfile changes as `deployment` and `schema`

## Findings

- What worked: initialization preserved existing non-NOC docs, validation passed, indexing worked, and lightweight change hints were clear.
- What was confusing: `suggest-map` correctly returned no suggestions, but users may need README guidance that no suggestions can be valid for flat CLI/tooling repositories.
- False positives: none observed.
- Missing coverage: this dogfood run covers a small repository only; a real monorepo and an existing-agent project still need manual dogfood runs before v1.
- Follow-up changes: document that `suggest-map` is advisory and may output an empty list for flat repositories.

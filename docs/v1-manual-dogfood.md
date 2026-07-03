# v1 Manual Dogfood

NOC Living Docs is close to small-but-hard v1 readiness, but v1 should not be declared until one real monorepo or multi-service dogfood run is recorded.

## Required User Input

Provide one local project path matching at least one condition:

- contains `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, or `rush.json`
- contains `apps/`, `packages/`, or `services/` with 3 or more child directories
- is otherwise a real multi-service or multi-domain project

Example:

```text
E:\code\your-monorepo
```

## Safety Rules

The dogfood run must not modify the original project directly.

Process:

1. Copy the target project to a temporary directory.
2. Exclude heavy/generated directories such as `.git`, `node_modules`, `target`, `build`, `dist`, `.next`, and `out`.
3. Run NOC commands only against the temporary copy.
4. Record results under `docs/migration-reports/YYYY-MM-DD-<project>.md`.

## Commands

```bash
python scripts/noc.py init <temp-copy> --mode auto
python scripts/noc.py validate --target <temp-copy>
python scripts/noc.py index <temp-copy>
python scripts/noc.py suggest-map <temp-copy>
python scripts/noc.py suggest-map <temp-copy> --write
python scripts/noc.py check <temp-copy> --staged --warn-only
```

## Acceptance Criteria

- Auto mode chooses Domain Mode for a clear multi-service or monorepo project.
- Existing agent files are preserved if present.
- Existing `docs/` or equivalent non-NOC documentation is left untouched.
- `suggest-map` returns useful service/domain-level paths.
- `suggest-map --write` appends paths without overwriting existing metadata.
- `validate` passes after initialization.
- Any `check` warning is understandable and advisory.

## v1 Gate Impact

After this report exists, the migration-report requirement in `docs/v1-readiness.md` can be considered satisfied.

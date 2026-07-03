# Token Policy

NOC Living Docs is designed for routing, not full-context loading.

## Modes

### Light Mode

Default for normal development.

Read:

- project agent entry file
- `noc_docs/docs-map.md`
- `.living-docs/feature-map.json` when available
- affected `agent-guide.md`
- affected `guardrails.md`

Read other feature docs only when needed.

### Deep Mode

Use for new features, complex refactors, migrations, API changes, security-sensitive changes, or cross-feature changes.

Also read:

- `requirements.md`
- `status.md`
- `test-record.md`
- `change-record.md`
- relevant domain docs

### Audit Mode

Use only when the user asks for initialization, documentation audit, migration, or full consistency review.

Audit Mode may scan the full `noc_docs/` tree.

### Query Mode

Use when answering questions about a feature, constraint, test, or requirement.

Route through `.living-docs/docs-index.json` or `docs-map.md`, then read the smallest relevant document set.

## Cache Principle

Use `.living-docs/` files as routing indexes and summaries. Do not treat them as the source of truth when they conflict with actual docs or code.


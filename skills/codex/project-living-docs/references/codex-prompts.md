# Codex Prompts

## Plan Mode

```text
Use NOC Living Docs to build the plan. Read only the affected feature docs, include required docs updates in the plan, and call out docs that are missing or stale.
```

## Goal Mode

```text
Use NOC Living Docs throughout this goal. Before coding, run `noc work` with `--json` for the affected path or feature. After changes, update related feature docs, then run index and check.
```

## Code Change After Requirement Discussion

```text
Use NOC Living Docs for this change.
First run `noc work <project> --path <code/path> --json` and write the agreed requirement into the related feature docs.
Then implement the code.
After implementation, update status, test-record, and change-record.
Run index and check.
```

## Docs Query

```text
Use NOC Living Docs to answer this. Route through feature-map and docs-index, then read only the relevant source docs.
```

## Migration

```text
Initialize NOC Living Docs for this project. Preserve existing docs and agent rules. Explain whether small or domain mode was selected and why.
```

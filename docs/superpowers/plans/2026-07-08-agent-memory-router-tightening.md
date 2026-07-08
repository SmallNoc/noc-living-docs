# Agent Memory Router Tightening Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Tighten NOC into a small, hard agent memory router by making `noc work --json` a stable routing contract, reducing default documentation weight, and keeping the product narrative focused on preventing agent context drift.

**Architecture:** Keep the existing single-file CLI shape in `scripts/noc.py` and add compatible fields to the JSON work plan instead of changing human-readable defaults. Tests in `tests/test_noc_cli.py` define the contract first, then documentation and NOC living docs are updated to match the tightened behavior.

**Tech Stack:** Python 3.10+, argparse, JSON, Markdown templates, unittest.

---

## File Structure

- Modify `scripts/noc.py`: work-plan data model, JSON output contract, path collection from Git, unresolved feature behavior.
- Modify `tests/test_noc_cli.py`: failing tests for schema fields, missing feature behavior, changed/staged path collection, and README/template contract.
- Modify `README.md`: shorten product story around agent memory routing and make full documentation structure feel optional rather than mandatory.
- Modify `templates/AGENTS.md`: keep the protocol small and focused on `noc work --json` routing.
- Modify `AGENTS.md`: regenerate or manually sync the managed block from `templates/AGENTS.md`.
- Modify `skills/codex/project-living-docs/SKILL.md`: align skill wording with the tighter work-plan contract.
- Modify `noc_docs/features/cli-core/*`: update requirements/status/test/change records for CLI behavior.
- Modify `noc_docs/features/agent-protocol/*`: update requirements/status/test/change records for agent protocol wording.
- Modify `noc_docs/features/release-quality/*`: record verification results.

## Task 1: Lock The Current Work JSON Contract

**Files:**
- Modify: `tests/test_noc_cli.py`
- Read: `scripts/noc.py`

- [x] **Step 1: Add a schema-focused failing test for `work --json`**

Add a test named `test_work_json_includes_stable_contract_fields`. Build a temporary project, create a `user-login` feature mapped to `src/auth/`, run:

```bash
python scripts/noc.py work <tmp-project> --path src/auth/login.py --json
```

Assert the JSON contains existing fields plus the new contract fields that will be implemented:

```python
self.assertEqual(plan["schema_version"], "1.0")
self.assertEqual(plan["resolution_status"], "resolved")
self.assertEqual(plan["features"][0]["id"], "user-login")
self.assertEqual(plan["features"][0]["matched_by"], "path")
self.assertEqual(plan["features"][0]["matched_path"], "src/auth/login.py")
self.assertEqual(plan["features"][0]["matched_pattern"], "src/auth/")
self.assertEqual(plan["features"][0]["confidence"], "high")
```

- [x] **Step 2: Run the new test and verify it fails**

Run:

```bash
python -m unittest tests.test_noc_cli.NocCliTests.test_work_json_includes_stable_contract_fields
```

Expected: FAIL because `schema_version`, `resolution_status`, and match metadata do not exist yet.

- [x] **Step 3: Implement compatible contract fields**

In `scripts/noc.py`, keep all existing JSON keys and add:

```python
"schema_version": "1.0"
"resolution_status": "resolved" | "unresolved" | "missing_feature"
```

For each feature plan, add:

```python
"matched_by": "feature" | "path" | "fallback"
"matched_path": str | None
"matched_pattern": str | None
"confidence": "high" | "low"
```

Do this by replacing `resolve_work_features()` with a resolver that returns structured match objects. Keep text output stable unless new metadata is harmless to omit from text mode.

- [x] **Step 4: Run the focused test**

Run:

```bash
python -m unittest tests.test_noc_cli.NocCliTests.test_work_json_includes_stable_contract_fields
```

Expected: PASS.

- [x] **Step 5: Run existing work tests**

Run:

```bash
python -m unittest tests.test_noc_cli.NocCliTests.test_work_outputs_docs_plan_for_named_feature tests.test_noc_cli.NocCliTests.test_work_resolves_feature_from_path_mapping tests.test_noc_cli.NocCliTests.test_work_json_outputs_machine_readable_plan
```

Expected: PASS.

## Task 2: Make Missing And Unresolved Routing Explicit

**Files:**
- Modify: `tests/test_noc_cli.py`
- Modify: `scripts/noc.py`

- [x] **Step 1: Add a failing test for unknown explicit feature**

Add `test_work_json_marks_missing_explicit_feature`. Run:

```bash
python scripts/noc.py work <tmp-project> --feature does-not-exist --json
```

Expected JSON:

```python
self.assertEqual(plan["resolution_status"], "missing_feature")
self.assertEqual(plan["features"][0]["id"], "does-not-exist")
self.assertEqual(plan["features"][0]["confidence"], "low")
self.assertIn("noc feature create", plan["next_actions"][0])
```

Do not make the command fail by default in this pass; keep compatibility and make the machine-readable status clear.

- [x] **Step 2: Add a failing test for unmatched path**

Add `test_work_json_marks_unresolved_path`. Run:

```bash
python scripts/noc.py work <tmp-project> --path unknown/file.py --json
```

Expected:

```python
self.assertEqual(plan["resolution_status"], "unresolved")
self.assertEqual(plan["features"][0]["id"], "unresolved")
self.assertEqual(plan["features"][0]["matched_by"], "fallback")
self.assertEqual(plan["features"][0]["confidence"], "low")
self.assertIn("noc suggest-map", " ".join(plan["next_actions"]))
```

- [x] **Step 3: Run both tests and verify they fail**

Run:

```bash
python -m unittest tests.test_noc_cli.NocCliTests.test_work_json_marks_missing_explicit_feature tests.test_noc_cli.NocCliTests.test_work_json_marks_unresolved_path
```

Expected: FAIL.

- [x] **Step 4: Implement `next_actions` and explicit statuses**

In `build_work_plan()`, add `next_actions`:

```python
[
  "Run: noc suggest-map <project> --interactive",
  "Run: noc feature create <project> <feature> --path <code/path>"
]
```

Use targeted actions:
- `missing_feature`: suggest `noc feature create`.
- `unresolved`: suggest `noc suggest-map` and then `noc feature create`.
- `resolved`: no `next_actions` or an empty list.

- [x] **Step 5: Run missing/unresolved tests**

Run the two focused tests again.

Expected: PASS.

## Task 3: Add Git-Derived Path Collection For Work Plans

**Files:**
- Modify: `tests/test_noc_cli.py`
- Modify: `scripts/noc.py`

- [x] **Step 1: Add failing test for `noc work --staged --json`**

Create a Git temp project, initialize NOC, create a feature mapped to `src/auth/`, stage `src/auth/login.py`, then run:

```bash
python scripts/noc.py work <tmp-project> --staged --json
```

Assert:

```python
self.assertEqual(plan["paths"], ["src/auth/login.py"])
self.assertEqual(plan["resolution_status"], "resolved")
self.assertEqual(plan["features"][0]["id"], "user-login")
```

- [x] **Step 2: Add failing test for `noc work --changed --json`**

Create an unstaged change and run:

```bash
python scripts/noc.py work <tmp-project> --changed --json
```

Assert the changed path is collected and routed.

- [x] **Step 3: Run both tests and verify they fail**

Run:

```bash
python -m unittest tests.test_noc_cli.NocCliTests.test_work_json_collects_staged_paths tests.test_noc_cli.NocCliTests.test_work_json_collects_changed_paths
```

Expected: FAIL because the options do not exist.

- [x] **Step 4: Add parser options**

In `build_parser()`, add to `work`:

```python
work.add_argument("--changed", action="store_true", help="Use changed Git paths from the working tree.")
work.add_argument("--staged", action="store_true", help="Use staged Git paths.")
```

If `--path` is also provided, combine and de-duplicate paths while preserving order. If both `--changed` and `--staged` are provided, combine both sets.

- [x] **Step 5: Implement path collection**

Reuse existing `changed_files(target, staged)`:

```python
paths = list(args.path or [])
if args.changed:
    paths.extend(changed_files(target, staged=False))
if args.staged:
    paths.extend(changed_files(target, staged=True))
paths = list(dict.fromkeys(paths))
```

Pass these paths into `build_work_plan()`.

- [x] **Step 6: Run focused tests**

Expected: PASS.

## Task 4: Reduce Default Documentation Weight In Product Narrative

**Files:**
- Modify: `README.md`
- Modify: `templates/AGENTS.md`
- Modify: `AGENTS.md`
- Modify: `skills/codex/project-living-docs/SKILL.md`
- Test: `tests/test_noc_cli.py`

- [x] **Step 1: Add text contract tests**

Extend existing tests so README and templates must contain the agent-router framing:

```python
self.assertIn("agent memory router", readme.lower())
self.assertIn("noc work <project> --path <code/path> --json", agents)
self.assertNotIn("must update every feature document", agents.lower())
```

Use wording checks sparingly; protect only the core promise.

- [x] **Step 2: Run focused text tests and verify they fail if wording is absent**

Run:

```bash
python -m unittest tests.test_noc_cli.NocCliTests.test_agent_entry_and_codex_skill_prefer_work_json
```

Expected: PASS or FAIL depending on the exact new assertions. If PASS, continue because the implementation is already compatible.

- [x] **Step 3: Rewrite README around the smaller promise**

Keep README short and explicit:
- NOC is an agent memory router.
- Default loop is `noc work --json`, read listed docs, update only changed facts, run `noc check`.
- Full seven-file feature docs are available, but not every file changes on every task.
- NOC does not replace wiki, ADR, issue tracker, release notes, dashboard, or model calls.

- [x] **Step 4: Tighten agent templates**

In `templates/AGENTS.md`, say:
- use `noc work --json` to route context
- read only listed docs
- update docs only when behavior, intent, tests, or constraints changed
- do not create a separate `docs/` root for the NOC protocol

Sync `AGENTS.md` managed block after template changes.

- [x] **Step 5: Tighten Codex skill wording**

In `skills/codex/project-living-docs/SKILL.md`, keep the final response format but make the purpose narrower: route project memory for code changes, avoid full-repo reading, avoid unnecessary doc churn.

## Task 5: Update NOC Living Docs For The New Contract

**Files:**
- Modify: `noc_docs/features/cli-core/requirements.md`
- Modify: `noc_docs/features/cli-core/status.md`
- Modify: `noc_docs/features/cli-core/change-record.md`
- Modify: `noc_docs/features/cli-core/test-record.md`
- Modify: `noc_docs/features/agent-protocol/requirements.md`
- Modify: `noc_docs/features/agent-protocol/status.md`
- Modify: `noc_docs/features/agent-protocol/change-record.md`
- Modify: `noc_docs/features/agent-protocol/test-record.md`
- Modify: `noc_docs/features/release-quality/test-record.md`

- [x] **Step 1: Update cli-core requirements**

Add acceptance criteria:
- JSON work plans include `schema_version`, `resolution_status`, match metadata, and `next_actions` when unresolved.
- `work --changed` and `work --staged` route Git paths without forcing agents to collect paths manually.

- [x] **Step 2: Update cli-core status**

Document the actual new behavior after implementation.

- [x] **Step 3: Append cli-core change record**

Add dated entry for the JSON contract and Git path collection.

- [x] **Step 4: Update agent-protocol docs**

Clarify that the protocol is route-first and update-only-when-needed.

- [x] **Step 5: Leave requirements unchanged where intent did not change**

Do not rewrite requirements just to mirror current implementation details.

## Task 6: Re-index, Verify, And Commit

**Files:**
- Generated/modified: `noc_docs/.living-docs/*`
- Modify: relevant docs from earlier tasks

- [x] **Step 1: Run index**

Run:

```bash
python scripts/noc.py index .
```

Expected: index files refresh without errors.

- [x] **Step 2: Run py_compile**

Run:

```bash
python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py
```

Expected: no output and exit code 0.

- [x] **Step 3: Run CLI tests**

Run:

```bash
python -m unittest tests.test_noc_cli
```

Expected: all tests pass.

- [x] **Step 4: Run release tests**

Run:

```bash
python -m unittest tests.test_release_cli
```

Expected: all tests pass.

- [x] **Step 5: Run validation**

Run:

```bash
python scripts/noc.py validate
python scripts/noc.py check . --staged --warn-only
```

Expected: validation passes; check returns 0. Any warnings must be explained and either fixed or accepted intentionally.

- [x] **Step 6: Review diff**

Run:

```bash
git diff --stat
git diff -- scripts/noc.py tests/test_noc_cli.py README.md templates/AGENTS.md AGENTS.md skills/codex/project-living-docs/SKILL.md
```

Expected: changes are scoped to the agent-router tightening goal.

- [x] **Step 7: Commit**

Run:

```bash
git add scripts/noc.py tests/test_noc_cli.py README.md templates/AGENTS.md AGENTS.md skills/codex/project-living-docs/SKILL.md noc_docs docs/superpowers/plans/2026-07-08-agent-memory-router-tightening.md
git commit -m "feat: tighten agent work routing"
```

Expected: commit succeeds.


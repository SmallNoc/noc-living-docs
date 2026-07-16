# Feature Archive MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use TDD task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not use superpower skills for this project unless the user explicitly re-enables them.

**Goal:** Build the confirmed NOC v2 feature-archive MVP while preserving old simplified and v1 projects without silent upgrades.

**Architecture:** Keep the user-facing flow as `noc setup`, `noc init`, then normal Codex requests. Move new feature-archive behavior into small modules under `scripts/noclib/` so `scripts/noc.py` remains the command dispatcher. Treat Markdown files as facts and JSON files as derived indexes or command payloads.

**Tech Stack:** Python 3.10+, stdlib only, `unittest`, existing subprocess-based CLI tests, existing `noc` console entry point.

---

## Global Compatibility Boundaries

- Existing `protocol_version: 2`, `layout: simplified`, `layout_version` missing or `1.0`: `work`, `index`, `doctor`, and `validate` are read-only with respect to project structure. They must not create `noc_docs/features/`, modify `config.json`, or modify `routing.json`.
- New `protocol_version: 2`, `layout: feature-archive`, `layout_version: 1.0`: supports project-level Markdown files plus `noc_docs/features/<feature-id>/overview.md`.
- Existing v1 `layout` inferred from `mode: small` or `mode: domain`: keeps the existing feature/domain behavior. v1 migration is explicit and dry-run first.
- `protocol_version` is not enough to distinguish behavior. All protocol decisions must use `protocol_version`, `layout`, and `layout_version`.

## File Structure

### New Modules

- Create `scripts/noclib/__init__.py`
  - Exports no runtime behavior. Keeps `scripts.noclib` importable in wheel and tests.
- Create `scripts/noclib/layouts.py`
  - Data structures:
    - `LayoutInfo(protocol_version: int | None, layout: str, layout_version: str | None, mode: str | None, documentation_root: str, config_path: Path | None)`
  - Functions:
    - `load_config(target: Path) -> dict`
    - `detect_layout(target: Path) -> LayoutInfo`
    - `is_simplified_v2(info: LayoutInfo) -> bool`
    - `is_feature_archive_v2(info: LayoutInfo) -> bool`
    - `is_v1_small(info: LayoutInfo) -> bool`
    - `is_v1_domain(info: LayoutInfo) -> bool`
- Create `scripts/noclib/schemas.py`
  - Constants:
    - `SUPPORTED_PROTOCOL_VERSION = 2`
    - `FEATURE_ARCHIVE_LAYOUT = "feature-archive"`
    - `FEATURE_ARCHIVE_LAYOUT_VERSION = "1.0"`
    - `SIMPLIFIED_LAYOUT = "simplified"`
    - `SIMPLIFIED_LAYOUT_VERSION = "1.0"`
    - `OVERVIEW_SCHEMA_VERSION = 1`
  - Functions:
    - `validate_config_schema(data: dict) -> list[str]`
    - `validate_overview_frontmatter(data: dict) -> list[str]`
    - `validate_candidate_payload(data: dict) -> list[str]`
    - `validate_feature_patch_payload(data: dict) -> list[str]`
    - `validate_evidence_payload(data: dict) -> list[str]`
    - `is_ascii_kebab_case(value: str) -> bool`
- Create `tests/test_feature_archive_stage1.py`
  - Stage 1 tests for schema validation, layout detection, validate/doctor recognition, and simplified no-write regression.

### Existing Files To Modify

- Modify `scripts/noc.py`
  - Replace local simplified/v1 layout checks with `scripts.noclib.layouts.detect_layout` in read-only paths used by `work`, `check`, and `doctor`.
  - Stage 1 does not change default `noc init`.
- Modify `scripts/index-noc-docs.py`
  - Use layout detection.
  - For simplified layout, preserve current behavior without adding `layout_version` or changing routing/config.
  - For feature-archive layout, Stage 1 only validates/read-recognizes. It does not generate new feature indexes yet.
- Modify `scripts/validate-noc-docs.py`
  - Use schema validation for feature-archive config and overview frontmatter.
  - Recognize feature-archive layout read-only.
- Modify `tests/test_simplified_memory.py`
  - Add regression coverage that old simplified `work`, `index`, `doctor`, and `validate` do not change file tree or hashes.
- Modify `pyproject.toml`
  - Phase 8 only, if package discovery needs `scripts.noclib`. Stage 1 verifies source-tree tests only; wheel package-data changes are release-readiness work.

### Files Not Modified In MVP Implementation Until Release Preparation

- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `.github/workflows/publish.yml`
- release tags or PyPI configuration

## Data Contracts

### Config Schema

Input file: `noc_docs/.living-docs/config.json`

Feature-archive required keys:

```json
{
  "protocol": "noc-living-docs",
  "protocol_version": 2,
  "layout": "feature-archive",
  "layout_version": "1.0",
  "documentation_root": "noc_docs",
  "language": "zh-CN",
  "machine_keys": "en-US",
  "feature_id_style": "ascii-kebab-case",
  "routing": {
    "high_confidence": 0.78,
    "medium_confidence": 0.55,
    "ambiguity_delta": 0.12
  }
}
```

Validation output: `list[str]` of error messages. Empty list means valid.

### Overview Frontmatter Schema

Input source: YAML-like frontmatter parsed by simple key reader in Stage 1.

Required keys:

```json
{
  "id": "user-login",
  "name": "用户登录",
  "status": "active",
  "schema_version": 1,
  "created_at": "2026-07-16",
  "updated_at": "2026-07-16",
  "language": "zh-CN"
}
```

Optional key:

```json
{"aliases": ["登录", "账号登录"]}
```

Validation rules:

- `id` must be ASCII kebab-case.
- `status` must be one of `proposed`, `active`, `deprecated`, `removed`.
- `schema_version` must be `1`.
- `name`, `created_at`, `updated_at`, and `language` must be non-empty strings.

### Candidate Payload Schema

Stage 1 validates shape only; Stage 3 produces it.

```json
{
  "schema_version": "1.0",
  "candidates": [
    {
      "id": "user-login",
      "name": "用户登录",
      "confidence": "high",
      "score": 0.86,
      "evidence": [{"type": "intent_alias", "value": "登录"}],
      "read_before_code": ["noc_docs/features/user-login/overview.md"]
    }
  ],
  "ambiguity": {"is_ambiguous": false, "top_delta": 0.31}
}
```

### Feature Patch Payload Schema

Stage 1 validates shape only; Stage 4 executes it.

Required top-level keys:

- `schema_version`
- `feature_id`
- `source`
- `patch`

Supported patch keys:

- `confirmed_requirements_add`
- `confirmed_requirements_update`
- `confirmed_requirements_remove`
- `implementation_updates`
- `constraints_add`
- `code_paths_add`
- `code_paths_remove`
- `verification_method_updates`
- `verification_result`
- `major_change_append`
- `pending_questions_add`
- `pending_questions_resolve`

Validation rules:

- `feature_id` must be ASCII kebab-case.
- `verification_result.result == "passed"` requires `verification_result.exit_code == 0`.
- `result` must be one of `passed`, `failed`, `not_run`, `unknown`.

### Evidence Payload Schema

Stage 1 validates shape only; Stage 5 records it.

```json
{
  "schema_version": "1.0",
  "code_evidence": {
    "mode": "staged",
    "changed_paths": ["src/auth/login.py"],
    "diff_summary": {"files_changed": 1, "insertions": 24, "deletions": 3},
    "commit": null,
    "signals": [{"type": "api", "path": "src/auth/login.py", "confidence": "medium"}]
  },
  "verification_evidence": [
    {
      "command": "python -m pytest tests/auth/test_login.py",
      "cwd": ".",
      "started_at": "2026-07-16T10:00:00+08:00",
      "finished_at": "2026-07-16T10:00:12+08:00",
      "exit_code": 0,
      "result": "passed",
      "scope": "用户登录",
      "output_summary": "3 passed"
    }
  ]
}
```

Validation rules:

- `code_evidence.mode` must be `staged`, `unstaged`, `changed`, or `unknown`.
- `verification_evidence[*].result == "passed"` requires `exit_code == 0`.
- `noc evidence --staged` in Stage 5 can emit only `code_evidence`; it cannot infer `passed`.

## Phase 1: Schema And Read-Only Layout Recognition

**Files:**
- Create: `scripts/noclib/__init__.py`
- Create: `scripts/noclib/layouts.py`
- Create: `scripts/noclib/schemas.py`
- Create: `tests/test_feature_archive_stage1.py`
- Modify: `scripts/noc.py`
- Modify: `scripts/index-noc-docs.py`
- Modify: `scripts/validate-noc-docs.py`
- Modify: `tests/test_simplified_memory.py`

### Task 1.1: Schema Validation Module

- [ ] **Step 1: Write failing schema tests**

Add tests in `tests/test_feature_archive_stage1.py`:

```python
def test_feature_archive_config_schema_accepts_required_shape(self): ...
def test_feature_archive_config_schema_rejects_missing_layout_version(self): ...
def test_overview_frontmatter_requires_ascii_kebab_id(self): ...
def test_patch_schema_rejects_passed_result_without_zero_exit_code(self): ...
def test_evidence_schema_rejects_passed_result_without_zero_exit_code(self): ...
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m unittest tests.test_feature_archive_stage1 -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.noclib'`.

- [ ] **Step 3: Implement minimal schemas**

Create `scripts/noclib/__init__.py` and `scripts/noclib/schemas.py` with the constants and validation functions listed above.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m unittest tests.test_feature_archive_stage1 -v`

Expected: PASS for schema tests.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/noclib/__init__.py scripts/noclib/schemas.py tests/test_feature_archive_stage1.py
git commit -m "feat: add feature archive schema validators"
```

Expected: commit succeeds.

### Task 1.2: Layout Detection Module

- [ ] **Step 1: Write failing layout detection tests**

Add tests:

```python
def test_detect_layout_recognizes_simplified_v2(self): ...
def test_detect_layout_recognizes_feature_archive_v2(self): ...
def test_detect_layout_recognizes_v1_small(self): ...
def test_detect_layout_recognizes_v1_domain(self): ...
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m unittest tests.test_feature_archive_stage1 -v`

Expected: FAIL with import or missing function error for `scripts.noclib.layouts`.

- [ ] **Step 3: Implement minimal layout detection**

Create `scripts/noclib/layouts.py` with `LayoutInfo`, `load_config`, `detect_layout`, and helper predicates.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m unittest tests.test_feature_archive_stage1 -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/noclib/layouts.py tests/test_feature_archive_stage1.py
git commit -m "feat: detect noc docs layouts"
```

Expected: commit succeeds.

### Task 1.3: Validate Recognizes Feature Archive Read-Only

- [ ] **Step 1: Write failing CLI validate tests**

Add tests that create a temporary feature-archive project with:

- `noc_docs/project.md`
- `noc_docs/guardrails.md`
- `noc_docs/verification.md`
- `noc_docs/features/user-login/overview.md`
- `noc_docs/.living-docs/config.json`
- `AGENTS.md` with the managed block markers

Assertions:

- `python scripts/noc.py validate --target <project>` returns 0.
- Invalid overview id returns non-zero.
- The command does not change file hashes.

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m unittest tests.test_feature_archive_stage1 -v`

Expected: FAIL because `validate-noc-docs.py` rejects protocol v2 layout other than `simplified`.

- [ ] **Step 3: Implement minimal validate support**

Modify `scripts/validate-noc-docs.py`:

- detect `layout == "feature-archive"` and `layout_version == "1.0"`
- require project-level three Markdown files
- require `noc_docs/features/` directory
- validate each `features/*/overview.md` frontmatter
- do not write files

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m unittest tests.test_feature_archive_stage1 -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/validate-noc-docs.py tests/test_feature_archive_stage1.py
git commit -m "feat: validate feature archive layout"
```

Expected: commit succeeds.

### Task 1.4: Doctor Recognizes Feature Archive Read-Only

- [ ] **Step 1: Write failing doctor tests**

Add tests:

```python
def test_doctor_reports_feature_archive_layout(self): ...
def test_doctor_feature_archive_does_not_modify_files(self): ...
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m unittest tests.test_feature_archive_stage1 -v`

Expected: FAIL because doctor currently handles only simplified v2 or v1 indexes.

- [ ] **Step 3: Implement minimal doctor support**

Modify `scripts/noc.py`:

- use `detect_layout`
- add feature-archive branch in `command_doctor`
- parse `config.json`
- check project-level files and overview files
- print `protocol 2 feature-archive layout is ready`
- do not write files

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m unittest tests.test_feature_archive_stage1 -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/noc.py tests/test_feature_archive_stage1.py
git commit -m "feat: recognize feature archive in doctor"
```

Expected: commit succeeds.

### Task 1.5: Simplified No-Write Regression

- [ ] **Step 1: Write failing no-write regression test**

Add test in `tests/test_simplified_memory.py`:

```python
def test_existing_simplified_work_index_doctor_validate_do_not_modify_files(self): ...
```

The test:

1. Creates a v2 simplified project through existing `noc init`.
2. Commits or snapshots file hashes.
3. Runs:
   - `python scripts/noc.py work <project> --path src/app.py --json`
   - `python scripts/noc.py index <project>`
   - `python scripts/noc.py doctor <project>`
   - `python scripts/noc.py validate --target <project>`
4. Compares file tree and SHA-256 hashes before and after.

- [ ] **Step 2: Run test to verify baseline**

Run: `python -m unittest tests.test_simplified_memory.SimplifiedProjectMemoryTests.test_existing_simplified_work_index_doctor_validate_do_not_modify_files -v`

Expected: PASS if current behavior is already safe. If FAIL, failure must identify the command that writes.

- [ ] **Step 3: Implement only if RED shows unsafe write**

If the test fails, modify only the command that writes:

- `work`: no writes.
- `doctor`: no writes.
- `validate`: no writes.
- `index`: for simplified, do not rewrite files when content is unchanged.

- [ ] **Step 4: Run regression test**

Run: `python -m unittest tests.test_simplified_memory.SimplifiedProjectMemoryTests.test_existing_simplified_work_index_doctor_validate_do_not_modify_files -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/noc.py scripts/index-noc-docs.py scripts/validate-noc-docs.py tests/test_simplified_memory.py
git commit -m "test: lock simplified layout read-only commands"
```

Expected: commit succeeds. If no production code changed, commit includes only the test.

### Task 1.6: Stage 1 Full Verification

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m unittest tests.test_feature_archive_stage1 -v
python -m unittest tests.test_simplified_memory -v
```

Expected: PASS.

- [ ] **Step 2: Run required project checks**

Run:

```bash
python -m unittest discover -s tests
python scripts/noc.py validate .
python scripts/release.py --check
```

Expected: PASS. If a command fails because of repository state unrelated to Stage 1, capture stdout/stderr and stop.

- [ ] **Step 3: Run explicit simplified no-write script**

Run a PowerShell script that:

1. Creates a temporary project.
2. Installs Skill into temporary `CODEX_HOME`.
3. Runs `noc init`.
4. Captures file list and SHA-256 hashes.
5. Runs `work`, `index`, `doctor`, `validate`.
6. Captures file list and hashes again.
7. Fails if any path or hash differs.

Expected: `NO_WRITE_OK`.

- [ ] **Step 4: Commit remaining Stage 1 verification or doc updates**

Run:

```bash
git status --short
git add <only-stage-1-files>
git commit -m "test: verify feature archive stage one"
```

Expected: commit succeeds only if files changed after the previous commit.

## Phase 2: New Init And Indexing

**Files:**
- Modify: `scripts/init-noc-docs.py`
- Modify: `scripts/index-noc-docs.py`
- Modify: `scripts/noc.py`
- Create: `scripts/noclib/overview.py`
- Modify: `tests/test_simplified_memory.py`
- Create: `tests/test_feature_archive_init.py`

Tasks:

1. Write failing tests that new `noc init` creates feature-archive config with `layout_version: "1.0"` and project-level three Markdown files, but no feature directories with placeholder files.
2. Implement `scripts/noclib/overview.py` helpers:
   - `render_overview_frontmatter(feature_id: str, name: str, aliases: list[str], today: str) -> str`
   - `parse_overview_frontmatter(text: str) -> dict`
3. Implement feature-archive init path in `scripts/init-noc-docs.py`.
4. Implement feature-archive `index` output:
   - `feature-index.json`
   - `routing.json`
   - `manifest.json`
5. Confirm old simplified projects are not converted by rerunning the Stage 1 no-write regression.
6. Commit each passing task independently.

Commands:

```bash
python -m unittest tests.test_feature_archive_init -v
python -m unittest tests.test_simplified_memory -v
```

Expected: PASS after implementation.

## Phase 3: Candidate Routing And Feature Ensure

**Files:**
- Modify: `scripts/noc.py`
- Create: `scripts/noclib/candidates.py`
- Create: `scripts/noclib/features.py`
- Create: `tests/test_feature_archive_routing.py`

New data structures:

- `Candidate(id: str, name: str, score: float, confidence: str, evidence: list[dict], read_before_code: list[str])`
- `CandidateResult(schema_version: str, candidates: list[Candidate], ambiguity: dict)`

Functions:

- `score_candidates(intent: str | None, paths: list[str], feature_index: dict, thresholds: dict) -> dict`
- `confidence_for_score(score: float, thresholds: dict) -> str`
- `ensure_feature(target: Path, feature_id: str, name: str, aliases: list[str]) -> dict`

Tasks:

1. Tests for high, medium, low, ambiguous, no candidate, intent/path conflict, and multi-feature outputs.
2. Tests for `feature ensure` idempotency and ASCII kebab-case rejection.
3. Implement `noc work` feature-archive candidate output.
4. Implement `noc feature ensure`.
5. Commit routing and ensure separately.

## Phase 4: Structured Feature Update

**Files:**
- Modify: `scripts/noc.py`
- Create: `scripts/noclib/patches.py`
- Modify: `scripts/noclib/overview.py`
- Create: `tests/test_feature_archive_update.py`

Functions:

- `apply_feature_patch(overview_text: str, patch: dict) -> tuple[str, dict]`
- `backup_file(path: Path, root: Path) -> Path`
- `atomic_write(path: Path, content: str) -> None`
- `normalize_entry_text(value: str) -> str`

Tasks:

1. Failing tests for each patch key.
2. Failing tests for duplicate suppression.
3. Failing tests for backup before write and atomic output.
4. Implement `noc feature update`.
5. Commit schema enforcement, patch application, and CLI command separately.

## Phase 5: Evidence And Check

**Files:**
- Modify: `scripts/noc.py`
- Create: `scripts/noclib/evidence.py`
- Modify: `scripts/noclib/schemas.py`
- Create: `tests/test_feature_archive_evidence.py`
- Create: `tests/test_feature_archive_check.py`

Functions:

- `collect_code_evidence(target: Path, staged: bool) -> dict`
- `summarize_diff(target: Path, staged: bool) -> dict`
- `detect_change_signals(paths: list[str], diff_text: str) -> list[dict]`
- `record_verification_evidence(target: Path, payload: dict) -> dict`
- `check_feature_archive_updates(target: Path, declared: list[str], staged: bool) -> dict`

Tasks:

1. Test that `noc evidence --staged` emits code evidence only.
2. Test that verification `passed` requires zero exit code.
3. Test that `noc check` accepts matching overview updates and rejects unrelated churn.
4. Implement commands.
5. Commit evidence and check separately.

## Phase 6: Migration And Rollback

**Files:**
- Modify: `scripts/noc.py`
- Create: `scripts/noclib/migration.py`
- Create: `tests/test_feature_archive_migration.py`

Functions:

- `plan_simplified_migration(target: Path) -> dict`
- `plan_v1_migration(target: Path) -> dict`
- `create_migration_backup(target: Path) -> Path`
- `apply_simplified_migration(target: Path, plan: dict) -> dict`
- `apply_v1_migration(target: Path, plan: dict) -> dict`

Tasks:

1. Test simplified dry-run writes nothing.
2. Test simplified apply requires backup.
3. Test v1 dry-run preserves every source file in report.
4. Test v1 uncertain semantic content goes to legacy appendix.
5. Test rollback instructions point to real backup.
6. Implement `noc migrate --dry-run`.
7. Implement `noc migrate --apply --backup`.
8. Commit dry-run and apply separately.

## Phase 7: Skill And User-Facing Docs

**Files:**
- Modify: `.agents/skills/project-living-docs/SKILL.md`
- Modify: `.agents/skills/project-living-docs/references/workflow.md`
- Modify: `.agents/skills/project-living-docs/references/feature-doc-template.md`
- Modify: `.agents/skills/project-living-docs/evals/project-living-docs.prompts.csv`
- Mirror same files under `skills/codex/project-living-docs/`
- Modify: `templates/AGENTS.md`
- Modify: `README.md`
- Modify: `tests/test_noc_cli.py`
- Modify: `tests/test_setup_cli.py`

Tasks:

1. Tests for Skill references to `feature update` and no direct overview rewrite.
2. Tests for README first screen still showing zero-learning flow.
3. Tests that both Skill trees stay synchronized.
4. Update Skill workflow.
5. Update README advanced details.
6. Commit Skill and README separately.

## Phase 8: Release-Readiness Verification Without Publishing

**Files:**
- Modify only if needed after user approval:
  - `pyproject.toml`
  - `CHANGELOG.md`
  - `VERSION`

Tasks:

1. Run full tests:

```bash
python -m py_compile scripts/__init__.py scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py
python -m unittest discover -s tests
python scripts/noc.py validate .
python scripts/release.py --check
python -m build
python -m twine check dist/*
```

2. Run isolated wheel journey:
   - install wheel in temporary venv
   - run `noc --version`
   - run `noc setup --json`
   - run new `noc init`
   - run feature-archive `work`, `feature ensure`, `feature update`, `index`, `check`
   - run old simplified no-write regression
3. Do not tag.
4. Do not publish.
5. Do not merge.

## Plan Self-Check

- Covers all confirmed MVP items: yes.
- Contains no placeholder markers or vague deferred implementation steps: yes.
- Function and field names are consistent across phases: yes.
- Excludes MVP non-goals from Phase 1 and keeps complex splitting, auto test execution, automatic v1 semantic migration, automatic deletion, and automatic feature-id rename out of MVP: yes.
- Prevents old project silent modification: yes; Stage 1 has a dedicated no-write regression and migration is explicit in Phase 6.
- Keeps Stage 1 within schema and read-only recognition: yes.

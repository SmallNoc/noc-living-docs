# Change Record: release-quality

## 2026-07-14 - Prepare v1.2.1 release metadata

- Used the tested release CLI patch bump to create the 1.2.1 changelog entry and update `VERSION`.
- Aligned package metadata, bilingual README markers, the canonical Skill manifest, current-version assertions, and current living-doc status at 1.2.1.
- Kept tagging, publishing, commits, and PR creation out of this preparation stage.

## 2026-07-14 - Record semantic memory updates in 1.2.0

- Extended the existing 1.2.0 Unreleased changelog entry with semantic memory-impact classification, `check --memory-impact`, no-churn Bug-fix behavior, and simplified final responses.
- Kept VERSION, package metadata, tagging, and publishing state unchanged.

## 2026-07-14 - Prepare the 1.2.0 development release

- Aligned VERSION, package metadata, README version markers, CHANGELOG, and the bundled Skill manifest at 1.2.0 Unreleased.
- Updated the publish workflow to run the complete test discovery and install the Skill before its simplified-init smoke test.
- Kept tagging, GitHub Release creation, and PyPI publishing out of this pull request.

## 2026-07-13 - Run setup coverage in remote release gates

- Added `tests.test_setup_cli` to the pull-request validation and tag publishing unittest commands.
- Installed the `build` test dependency in PR validation so the wheel isolation test runs instead of failing before package construction.
- Updated the canonical testing command so local and remote release gates execute the same stage 1 setup coverage.

## 2026-07-13 - Verify the CLI-to-Skill installation bundle

- Added isolated CODEX_HOME setup tests for install, check, repair, upgrade, collision protection, JSON, and cross-platform path composition.
- Added a wheel archive assertion for the Skill manifest and runtime references.
- Kept the release version and publishing workflow unchanged.
- Release review added repository-external wheel execution, Unicode/space path coverage, JSON error-contract checks, managed-identity forgery protection, and interrupted-copy cleanup tests.

## 2026-07-10 - Make staged-check tests independent of global Git identity

### Reason

The PyPI publish workflow runs tests on GitHub-hosted runners that do not have a global Git `user.name` or `user.email`. Several `noc check --staged` tests create temporary Git repositories and intentionally ignore the return code from their baseline commit. Without local Git identity, that baseline commit failed silently, leaving generated `noc_docs/` files staged and masking the code-only staged changes the tests were meant to verify.

### Changed

- Configured local test Git identity immediately after each temporary `git init` in `tests/test_noc_cli.py`.
- Kept the product `noc check` file classification and trigger logic unchanged.

### Impact

- The staged-check tests now exercise the same code/doc mismatch behavior in CI and on developer machines, including code classification for Python, JavaScript, TypeScript, Tcl, SKILL, YAML, SQL, shell, Dockerfile, Java, Go, and migration-heavy projects.

## 2026-07-10 - Isolate release tests from GitHub tag environment

### Reason

The PyPI publish workflow runs tests on a tag event, so GitHub sets `GITHUB_REF_TYPE=tag` and `GITHUB_REF_NAME=v1.0.2`. Release helper tests create temporary projects with their own versions, such as `0.4.0`; inheriting the outer tag environment made those temp-project checks fail even when the repository release version was correct.

### Changed

- Updated the release test helper to remove GitHub tag environment variables by default.
- Kept the explicit GitHub tag mismatch test opt-in by passing the tag environment only for that test.

### Impact

- The publish workflow can run the release helper test suite under `v1.0.2` tag events without false version mismatch failures.

## 2026-07-10 - Bump PyPI release target to 1.0.2

### Reason

The local `v1.0.1` tag already exists and points at an older release commit, so the PyPI publishing work needs a new tag instead of rewriting the existing tag.

### Changed

- Bumped `VERSION`, `pyproject.toml`, README current-version text, and release examples to `1.0.2`.
- Moved unreleased changelog notes into a `1.0.2` release entry.

### Impact

- Release bookkeeping can create and push `v1.0.2` without rewriting the existing `v1.0.1` tag.

## 2026-07-10 - Add PyPI publishing readiness

### Reason

The project needs to publish a real `noc-living-docs` package to PyPI so users can install the CLI with `pipx install noc-living-docs` after release.

### Changed

- Updated `pyproject.toml` for modern license metadata, project URLs, explicit package discovery, and package data that includes hidden `.living-docs` template JSON files without pycache files.
- Added `.github/workflows/publish.yml` for tag-triggered PyPI publishing through Trusted Publishing and OIDC.
- Added `docs/release.md` with local build/twine/test checks and manual PyPI Trusted Publishing setup steps.
- Extended `scripts/release.py --check` to verify `pyproject.toml` and README version consistency.
- Added tests for package metadata, publish workflow requirements, release docs, and version mismatch failures.
- Ignored local build artifacts in `.gitignore`.

### Impact

- Maintainers can build and verify PyPI artifacts locally, then publish from a `v*` tag without storing PyPI credentials in the repository.

## 2026-07-09 - Standardize install guidance and version metadata

### Reason

The README pointed users at package install commands that may fail before PyPI publication, and `pyproject.toml` still declared `1.0.0` while other release files declared `1.0.1`.

### Changed

- Updated README English and Chinese install guidance to recommend `pipx install git+https://github.com/SmallNoc/noc-living-docs.git` until PyPI publishing is available.
- Added project-level and global Codex skill copy instructions for `.agents/skills/project-living-docs/`.
- Added GitHub topic suggestions and clearer first-sentence positioning.
- Bumped `pyproject.toml` to `1.0.1` and expanded package keywords.

### Impact

- New users get a currently usable install command, Codex users can find the standard skill path, and release metadata is consistent.

## 2026-07-08 - Cover agent-first work plan behavior

### Reason

Structured work output and agent entry guidance are core usability behavior and should be regression-tested.

### Changed

- Added unittest coverage for `work --json`.
- Added unittest coverage that agent entry and Codex skill prefer JSON work plans.

### Impact

- Future changes are less likely to remove the agent-first path accidentally.

## 2026-07-08 - Strengthen README product entry

### Reason

The previous README preserved the small agent memory router framing but was too sparse to explain the problem, show the workflow, or build confidence for new users.

### Changed

- Expanded README with problem framing, a JSON work-plan example, quick start, agent workflow, comparison table, and coding-agent guidance.
- Added `README.md` to the release-quality feature mapping so future README edits route to a concrete feature.

### Impact

- New users can understand both the product value and the exact command loop without reading deeper docs first.

## 2026-07-08 - Prepare 1.0.1 release

### Reason

The agent-usability work needs to become the version published from `main`, with a new tag instead of moving the existing `v1.0.0` tag.

### Changed

- Bumped `VERSION` to `1.0.1`.
- Updated `CHANGELOG.md` with the agent routing and README improvements.

### Impact

- Release bookkeeping can create a new `v1.0.1` tag without rewriting prior tags.

## 2026-07-08 - Expand bilingual README usage guide

### Reason

The README still under-explained update flow, command coverage, generated document structure, and file responsibilities. The English and Chinese sections also needed to stay structurally aligned.

### Changed

- Expanded README with install, update, quick start, daily use, agent workflow, commands, generated documents, document responsibilities, machine files, domain mode, comparisons, and agent usage.
- Mirrored the same structure in Chinese.
- Corrected the displayed current version to `1.0.1`.

### Impact

- New users can understand how to install, update, initialize, use, and maintain NOC without jumping into deeper docs first.

## 2026-07-13 - Prepare 1.1.0 installation release

### Reason

The completed stage 1 installation closure adds the user-visible `noc setup` command family and therefore requires a backward-compatible minor release.

### Changed

- Bumped the formal release sources to `1.1.0` and documented the setup installation closure in `CHANGELOG.md` and README.
- Extended the release check to require the bundled Skill manifest version to match `VERSION`.

### Impact

- Release preparation now catches CLI/package/Skill version drift before packaging, while leaving the v1.0.2 document protocol and existing commands unchanged.

## 2026-07-14 - Finalize the 1.2.0 entry experience

### Changed

- Replaced the README first screen with install, one-time initialization, and normal Codex use.
- Moved legacy and maintenance command guidance under Advanced usage without removing it.
- Extended the isolated wheel test through simplified initialization and semantic memory checks.

### Impact

- A new user can reach working project memory without learning NOC's internal command vocabulary.

## 2026-07-14 - Align v1.2.0 documentation, Skill, and CI

### Changed

- Corrected the README workflow badge and made the primary English and Chinese guidance match default v2 simplified initialization.
- Split the synchronized Skill Definition of Done into v2 simplified and v1 legacy rules.
- Switched Validate CI to unittest discovery and added consistency regression tests.
- Narrowed agent compatibility claims to behavior supported by implementation and tests.

### Impact

- The v1.2.1 patch can restore documentation and release-gate consistency without adding features or changing version metadata.

# Migration Report: mySpringBoot

Date: 2026-07-04

## Project

- Repository: local `E:\code\mySpringBoot`
- Stack: Spring Boot 3.3.x, Java 17, Maven
- Shape: small single-module service
- Existing docs: none observed in the temporary dogfood copy
- Existing agent files: `AGENTS.md`

## Commands

Executed against a temporary copy of the project:

```bash
python scripts/noc.py init <temp-copy> --mode auto
python scripts/noc.py validate --target <temp-copy>
python scripts/noc.py index <temp-copy>
python scripts/noc.py suggest-map <temp-copy>
```

## Results

- Selected mode: `small`
- Created files: 17
- Updated files: appended the NOC managed block to existing `AGENTS.md`
- Preserved files: existing `AGENTS.md` project rules remained outside the managed block
- Validation: passed
- Index: generated 13 indexed documents
- Suggest map: produced Java package-level candidates:
  - `api` -> `src/main/java/com/noc/code/api/`
  - `application` -> `src/main/java/com/noc/code/application/`
  - `common` -> `src/main/java/com/noc/code/common/`
  - `domain` -> `src/main/java/com/noc/code/domain/`
  - `infrastructure` -> `src/main/java/com/noc/code/infrastructure/`

## Findings

- What worked: existing agent rules were preserved, initialization chose the lightweight layout, validation passed, and Java package mapping produced useful candidates.
- What was confusing: the first `suggest-map` implementation suggested `src/main/` and `src/test/`, which was too coarse for Maven projects.
- False positives: `src/test/` was initially suggested as a feature path; fixed by using Java package branches and skipping `src/main` / `src/test` as feature names.
- Missing coverage: this covers an existing-agent Java project, not a monorepo.
- Follow-up changes: keep Java package branch detection covered by tests before v1.

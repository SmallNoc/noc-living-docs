# Git Workflow

## Branches

- Use `feature/<short-name>` for features.
- Use `fix/<short-name>` for fixes.
- Use `docs/<short-name>` for documentation-only changes.

## Commit Messages

Use Conventional Commits:

- `feat: add password reset`
- `fix: handle expired sessions`
- `docs: update login status`
- `test: add login lockout tests`
- `refactor: simplify auth service`

## Commit Scope

每个 commit 应该包含一个清晰、完整的改动。行为变更对应的文档更新应尽量和代码放在同一个 commit 中。

## Forbidden

- Do not use `git reset --hard` without explicit user approval.
- Do not force push without explicit user approval.
- Do not commit secrets, credentials, `.env`, or local machine paths.


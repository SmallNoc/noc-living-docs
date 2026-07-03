# Document Structure

NOC Living Docs supports two layouts.

## Small Mode

Use when a project has fewer than 20 identifiable features, fewer than 3 business domains, and no strong domain-level guardrails.

```text
noc_docs/
  project-status.md
  docs-map.md
  development/
    git-workflow.md
    testing.md
    documentation-policy.md
  features/
    index.md
    <feature-id>/
      agent-guide.md
      requirements.md
      status.md
      guardrails.md
      test-record.md
      change-record.md
      notes.md
  .living-docs/
    config.json
    manifest.json
    feature-map.json
    docs-index.json
```

## Domain Mode

Use when the project has 20 or more features, 3 or more business domains, 3 or more apps/services, a monorepo layout, or domain-level guardrails.

```text
noc_docs/
  project-status.md
  docs-map.md
  development/
    git-workflow.md
    testing.md
    documentation-policy.md
  domains/
    index.md
    <domain-id>/
      index.md
      guardrails.md
      features/
        <feature-id>/
          agent-guide.md
          requirements.md
          status.md
          guardrails.md
          test-record.md
          change-record.md
          notes.md
  .living-docs/
    config.json
    manifest.json
    feature-map.json
    docs-index.json
```

## Mode Decision

Default to Small Mode.

Use Domain Mode when any strong signal exists:

- `feature_count >= 20`
- `domain_count >= 3`
- `service_or_app_count >= 3`
- monorepo detected
- domain-level guardrails are required

Never initialize both `features/` and `domains/` for the same project unless the user explicitly requests migration planning.


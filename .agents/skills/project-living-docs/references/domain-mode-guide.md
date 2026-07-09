# Domain Mode Guide

Domain mode is for projects where feature docs need another grouping layer.

Use domain mode when one or more are true:

- the repo has 20 or more features
- there are 3 or more business domains
- there are 3 or more apps/services
- a monorepo is detected
- domain-level guardrails are needed
- top-level project directories represent separate products or services

## Layout

```text
noc_docs/
└─ domains/
   └─ <domain>/
      ├─ guardrails.md
      └─ features/
         └─ <feature>/
            ├─ agent-guide.md
            ├─ requirements.md
            ├─ status.md
            ├─ guardrails.md
            ├─ test-record.md
            ├─ change-record.md
            └─ notes.md
```

## Domain Guardrails

Use `noc_docs/domains/<domain>/guardrails.md` for constraints shared by multiple features in the same domain.

Examples:

- all billing features must preserve audit logs
- all auth features must keep existing token compatibility
- all reporting features must not change export schemas without migration notes

Feature `guardrails.md` may add narrower constraints but should not contradict domain guardrails.

## Mode Decision Output

When choosing domain mode, explain the concrete trigger:

```text
Domain Mode because this repo has 4 services and shared domain-level guardrails.
```

Do not initialize both `noc_docs/features/` and `noc_docs/domains/` unless the user explicitly asks for migration planning.

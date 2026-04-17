# Task Plan Input

Create a constrained task plan for a single-user local-first repo agent.

Goal:
{{GOAL}}

Repository context:
{{REPO_CONTEXT_JSON}}

Use `memory_context` when it helps clarify standing preferences, reusable workflows, or durable semantic context.

Use `github_context` when it is available to keep pull request and issue-comment plans aligned with recent open collaboration state.

The plan must stay within repository maintenance, docs, ADR, or small code-change work.

Supported file operation modes: `rewrite`, `replace_text`, `insert_after`, `append_text`, `create_file`, `copy_file`, `move_file`, and `delete_file`.

Prefer `replace_text`, `insert_after`, or `append_text` over `rewrite` when a deterministic local edit is enough.

Prefer `create_file` for new tracked text files and `copy_file` when starting from an existing tracked-safe template.

Use `move_file` or `delete_file` only when the goal explicitly requires destructive tracked-file lifecycle changes.

Destructive repo ops require separate `destructive-repo-write` approval, so prefer non-destructive edits when they are sufficient.

Allowed validation refs: {{ALLOWED_VALIDATION_REFS}}.

Use `validation_catalog` from the repository context as the source of truth.

Prefer returning validation command ids instead of raw commands when possible.

Return one branch name, one or more file operations, zero or more validation commands, one commit message, one draft pull request payload, and an optional issue comment payload.

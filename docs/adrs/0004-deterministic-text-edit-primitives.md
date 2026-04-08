# ADR 0004: Deterministic Text-Edit Primitives For Task-Agent Runs

- Status: Accepted
- Date: 2026-04-08

## Context

The CLI-first task-agent MVP could plan and execute constrained repo tasks, but its edit path was biased toward whole-file rewrites. That made small changes less auditable, less predictable, and harder to validate as the public repository surface matured.

At the same time, the project needed a clearer public engineering baseline for task runs: tracked validation commands, a minimal CI loop, and GitHub review templates that matched the runtime's real safety boundary.

## Decision

We will extend the task-agent with deterministic text-edit primitives for small tracked-file changes.

The supported task edit modes are:

- `rewrite`
- `replace_text`
- `insert_after`
- `append_text`

Planner output now declares the intended edit mode and high-level instructions. The provider materializes local edit modes into explicit payloads, and the workspace applies them with deterministic checks such as exact match counts and anchor validation.

Task validation commands move into tracked config at `configs/task/validation.yaml`. The runtime and GitHub Actions CI both read this tracked definition instead of relying on hard-coded command allowlists in code.

## Consequences

Positive:

- small doc and text-heavy repo changes become more reviewable and more predictable
- `task inspect` and ledger events now preserve the materialized edit payload instead of hiding all detail behind a rewritten file
- validation commands are explicit tracked behavior, not an implementation detail
- the public repo gains a minimum Windows-first CI and template baseline that matches the runtime contract

Tradeoffs:

- edits remain text-native and conservative; this does not add AST-aware refactors or arbitrary shell automation
- planner/provider complexity increases because non-rewrite edits require an extra materialization step
- Windows-first validation is explicit for now, so portability work remains future scope

## Rejected Alternatives

- Whole-file rewrite only: rejected because it obscures intent and overreaches on small edits.
- Arbitrary shell commands for validation: rejected because it weakens governance and public auditability.
- AST-first editing: rejected for this milestone because the repository still benefits more from transparent text operations than from language-specific mutation infrastructure.

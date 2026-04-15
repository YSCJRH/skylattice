# ADR 0008: Non-Destructive Repo Ops Primitives

- Status: Accepted
- Date: 2026-04-15

## Context

Skylattice already supported deterministic text edits and safer validation envelopes, but task-agent still had an awkward gap around non-destructive file-level work:

- creating a new tracked file relied on `rewrite` plus `create_if_missing`, which obscured intent
- copying a tracked template into a new file path had no first-class primitive
- destructive primitives such as delete or move were still incompatible with the current deny-by-default governance boundary

That meant the runtime could edit files safely, but it still lacked explicit operations for common scaffolding workflows such as creating a new doc or copying a tracked template.

## Decision

We add explicit non-destructive repo operation primitives before considering destructive ones.

Key decisions:

- support `create_file` as a first-class task operation for new tracked-safe text files
- support `copy_file` as a first-class task operation for copying tracked-safe text templates into new destinations
- keep both operations inside the existing repo-write tier and materialized step inspection path
- do not add delete or move primitives in this slice because current governance intentionally denies destructive actions by default

## Consequences

Positive:

- task plans can now express scaffolding intent more clearly
- `task inspect` and ledger payloads distinguish file creation and template copying from rewrites
- common repo workflows such as task briefs and doc scaffolds become easier to automate without widening destructive scope

Tradeoffs:

- the planner/provider contract gains more operation modes
- `create_file` and `copy_file` remain text-first and refuse existing destinations
- richer file operations now exist, but destructive file lifecycle management is still deferred

## Rejected Alternatives

- continue overloading `rewrite` for all new-file work: rejected because it hides intent
- add delete and move primitives now: rejected because governance and recovery semantics for destructive steps need a separate milestone
- add binary-aware file ops: rejected because the repository still benefits more from tracked text primitives than from broader asset mutation support

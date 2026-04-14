# Governance

Skylattice stays proactive by making permission and promotion boundaries explicit.

## Permission Tiers

- `observe`: local read-only activity
- `local-safe-write`: reversible writes under approved `.local/` roots
- `repo-write`: tracked repository writes initiated by task runs
- `external-read`: GitHub discovery for the technology radar
- `external-write`: remote GitHub writes for task runs
- `radar-experiment-write`: internal gate for radar spike artifacts on whitelisted paths
- `radar-promote-main`: internal gate for radar promotion writes on whitelisted paths
- `self-modify`: direct policy or autonomy widening

## Current Policy

Auto-approved from tracked policy:

- `observe`
- `local-safe-write`
- `external-read`
- `radar-experiment-write`
- `radar-promote-main`

Explicit approval required:

- `repo-write`
- `external-write`
- `self-modify`

## Task-Agent Validation Guard

Task validation is intentionally narrow.

- task-agent validation commands are limited to exact entries in `configs/task/validation.yaml`
- the tracked validation config is shared by the runtime and GitHub Actions CI
- planning a validation step does not grant arbitrary shell access or widen operator approvals
- validation refs resolve to tracked command ids, expected return codes, and optional stdout/stderr checks
- deterministic text-edit primitives still require `repo-write`; validation commands stay in the `observe` tier

## Recovery Guard

Recovery is explicit rather than automatic.

- blocked and halted runs require an operator-driven `task resume`
- repo-write and external-write failures can be retryable, but Skylattice must surface the failing step, required approval, and side-effect risk first
- resume-safe GitHub sync prefers branch-scoped PR reuse and deduplicated issue comments over blind replay
- no background retry worker is allowed in the current architecture

## Repo Operation Boundary

Richer repo operations are still intentionally narrow.

- non-destructive tracked file creation and template copying are allowed through explicit task primitives
- destructive file lifecycle actions such as delete or move remain out of scope for the current runtime slice
- this keeps repo automation useful for scaffolding work without weakening the default destructive guard

## Radar-Specific Guards

Auto-approved does not mean unbounded. Radar writes still pass extra gates in code:

- the worktree must be clean before scan, promotion, or rollback
- the base branch must be `main`
- changed paths must remain inside `configs/radar/promotion.yaml`
- promotions must satisfy score, validation, weekly-cap, and freeze checks
- repeated promotion failures trigger freeze mode in local radar state

## Destructive Action Handling

Destructive intent keywords still force denial unless the operator explicitly intervenes. Automatic radar behavior does not include reset, delete, purge, force-push, merge, or rebase paths.

## Memory Rules

- profile memory is never updated by the radar automatically
- episodic, semantic, and procedural memory can be written by radar runs, but each write must carry run provenance
- working memory is tombstoned at run close

## Freeze Mode

There are now two freeze concepts:

- tracked governance freeze mode from `configs/policies/governance.yaml`
- local radar freeze mode stored in SQLite after repeated promotion failures

Either one blocks automatic promotion. The tracked mode is an operator policy switch; the radar-local mode is an automatic safety response.

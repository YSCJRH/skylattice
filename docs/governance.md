# Governance

Skylattice stays proactive by making permission and promotion boundaries explicit.

## Permission Tiers

- `observe`: local read-only activity
- `local-safe-write`: reversible writes under approved `.local/` roots
- `repo-write`: tracked repository writes initiated by task runs
- `destructive-repo-write`: explicit companion approval for destructive tracked repo lifecycle steps
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

Additional operator gate:

- `destructive-repo-write` is not a general policy tier for routine planning; it is a second explicit approval that must accompany destructive tracked repo actions such as `move_file` and `delete_file`

## Hosted Web Control Plane Guard

- the hosted app can authenticate users, pair devices, and queue command intent, but it does not create a new permission tier
- every hosted-app-triggered command still resolves to the same local governance checks inside the paired runtime
- browser ergonomics do not authorize silent repo writes, external writes, or destructive repo actions
- a paired connector may claim commands automatically, but any blocked or approval-gated runtime step still remains blocked until the local runtime rules allow it

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
- the hosted control plane also does not authorize background retry bypass; connector polling may claim work, but failing steps still surface through governed local recovery

## Repo Operation Boundary

Richer repo operations are still intentionally narrow.

- non-destructive tracked file creation and template copying are allowed through explicit task primitives
- destructive tracked file lifecycle actions now exist as explicit task primitives: `move_file` and `delete_file`
- destructive repo ops require both `repo-write` and `destructive-repo-write`
- destructive repo ops stay text-first and file-scoped: no directory delete/move support and no reset/rebase/force-push paths

## Radar-Specific Guards

Auto-approved does not mean unbounded. Radar writes still pass extra gates in code:

- the worktree must be clean before scan, promotion, or rollback
- the base branch must be `main`
- changed paths must remain inside `configs/radar/promotion.yaml`
- promotions must satisfy score, validation, weekly-cap, and freeze checks
- repeated promotion failures trigger freeze mode in local radar state

## Destructive Action Handling

Destructive intent keywords still force denial unless the operator explicitly grants the separate destructive approval. Automatic radar behavior still does not include reset, purge, force-push, merge, or rebase paths.

## Memory Rules

- profile memory is never updated by the radar automatically
- episodic, semantic, and procedural memory can be written by radar runs, but each write must carry run provenance
- working memory is tombstoned at run close

## Freeze Mode

There are now two freeze concepts:

- tracked governance freeze mode from `configs/policies/governance.yaml`
- local radar freeze mode stored in SQLite after repeated promotion failures

Either one blocks automatic promotion. The tracked mode is an operator policy switch; the radar-local mode is an automatic safety response.

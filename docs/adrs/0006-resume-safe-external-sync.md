# ADR 0006: Resume-Safe External Sync And Recovery Metadata

- Status: Accepted
- Date: 2026-04-15

## Context

Skylattice already supported paused task runs and explicit `task resume`, but the recovery surface was still too thin for a governed runtime:

- halted runs exposed an error, but not enough structured guidance about what to retry next
- operator-facing inspect surfaces did not summarize resumability, required approvals, or side-effect risk
- GitHub issue comments were vulnerable to duplicate writes if a failure happened after the remote side effect but before the local step completed cleanly

That gap mattered more once deterministic text edits and memory-backed planning were in place. The next operational risk was no longer "can the task run at all?" but "can the operator recover safely when the run is interrupted?"

## Decision

We make Phase 4 recovery behavior explicit and resume-safe without widening autonomy.

Key decisions:

- expose run-level recovery summaries through inspect, CLI status, and a read-only API endpoint
- record per-step retry metadata such as `attempt_count`, `last_error`, and `previous_errors`
- treat halted repo-write and external-write failures as retryable with structured operator guidance
- keep pull-request sync branch-scoped and explicitly surface whether a resume reused an existing PR
- make issue-comment sync deduplicated on resume through a stable per-run marker
- keep all recovery behavior local and operator-triggered; there is no background retry loop

## Consequences

Positive:

- operators can tell whether a run is resumable and which approval is needed next
- resumed GitHub sync is less likely to create duplicate public artifacts
- inspect surfaces become more useful for audit, debugging, and handoff

Tradeoffs:

- GitHub issue comments now carry a small hidden marker used for deduplication
- recovery logic is more stateful than the earlier MVP, even though it still fits inside the existing run/step model
- resume safety improves, but external APIs can still fail in ways that require manual operator judgment

## Rejected Alternatives

- silent automatic retries: rejected because they hide mutation timing and can obscure side effects
- a separate recovery queue: rejected because run steps already provide the durable retry surface
- broad external idempotency abstraction across all adapters now: rejected because the current priority is GitHub task sync, not a generic distributed job framework

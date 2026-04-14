# ADR 0009: GitHub Sync Context And Issue Preflight

- Status: Accepted
- Date: 2026-04-15

## Context

Skylattice already supported resume-safe draft PR reuse and deduplicated issue comments, but task-agent still lacked a bounded planning view of live GitHub collaboration state:

- planner prompts could not see recent open issues or pull requests even when GitHub was configured
- issue-comment sync could still fail late because the target issue state was only discovered at write time
- the roadmap called for better issue and PR synchronization behavior without turning GitHub into runtime truth

## Decision

We add a bounded GitHub sync context for planning and an observe-tier issue preflight before comment sync.

Key decisions:

- when GitHub is configured, repo context includes a small read-only snapshot of recent open issues and open PRs
- this `github_context` remains advisory planning context, not operational truth
- issue-comment plans now insert an observe-tier `github.inspect_issue` step before the external-write comment step
- preflight requires the target issue to be open before comment sync proceeds

## Consequences

Positive:

- planner prompts can stay more consistent with active repository collaboration state
- comment sync avoids writing blindly to closed or missing issues
- GitHub collaboration becomes safer without introducing background sync or broad automation

Tradeoffs:

- planner context becomes slightly larger when GitHub is configured
- issue comments now incur one additional read step before the write step
- stale remote state is still possible between preflight and write, so this is safer but not perfect synchronization

## Rejected Alternatives

- full issue and PR mirroring into local runtime state: rejected because GitHub remains an audit and collaboration layer, not runtime truth
- skipping preflight and relying on write failures only: rejected because it delays basic state validation until after the plan has already reached the external-write boundary
- broad review-thread automation now: rejected because it widens the collaboration surface faster than the current governance model is ready for

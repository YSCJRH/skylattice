# ADR 0017: GitLab As The Second Live Radar Provider

## Status

Accepted

## Context

Phase 5 established the radar provider contract, provider-neutral identity, provider-neutral adoption matching, and normalized evidence taxonomy, but GitHub remained the only live source.

That left one important product question unresolved: was the provider-neutral radar architecture a real operational seam, or only a well-prepared abstraction around one provider?

The next bounded wedge should answer that question without reopening broader product scope such as AST-aware task edits, multi-source fusion, resident scheduling, or autonomy expansion.

## Decision

GitLab becomes the second live radar provider in the next slice.

Key decisions:

- implement a dedicated read-only GitLab adapter for radar use
- add `GitLabRadarSource` behind the existing `RadarDiscoverySource` protocol
- ship GitLab as a live tracked provider entry while keeping GitHub as the default provider
- scope the first live GitLab slice to `gitlab.com` and explicit `GITLAB_TOKEN`
- keep one-provider-per-scan behavior through tracked config; no multi-source aggregation in this slice
- keep task-agent collaboration behavior GitHub-only; this slice is radar-only

## Consequences

### Positive

- Skylattice proves that its provider-neutral radar contract can support a real second source
- the next wedge extends an existing architectural lane instead of reopening multiple runtime boundaries at once
- candidate identity, evidence taxonomy, and adoption matching are validated against more than one provider shape

### Negative

- auth diagnostics and public docs become slightly more complex because radar now has another explicit credential path
- GitLab.com-first rollout defers self-managed GitLab questions to a later slice
- release and public-readiness surfaces must stay precise about GitHub remaining the default provider

## Non-Goals

- this ADR does not introduce multi-source fusion in one radar scan
- it does not add GitLab task-agent sync or GitLab issue/PR collaboration behavior
- it does not add a resident scheduler, broader autonomy, or AST-aware task edits

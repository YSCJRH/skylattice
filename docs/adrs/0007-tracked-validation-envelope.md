# ADR 0007: Tracked Validation Envelope

- Status: Accepted
- Date: 2026-04-15

## Context

Skylattice already constrained task validation to commands listed in tracked config, but the envelope was still relatively thin:

- validation steps were identified by raw command strings only
- runtime verification mostly checked return code, not richer expectations
- CI and local validation shared a command list, but not stable command identities or profiles

That made the validation boundary better than arbitrary shell execution, but still less legible and less reusable than the rest of the tracked system surface.

## Decision

We evolve task validation from a plain allowlist into a tracked validation envelope.

Key decisions:

- each tracked validation command gets a stable `id`
- validation config can declare `expected_returncode`, `stdout_contains`, and `stderr_contains`
- tracked profiles group validation command ids for shared runtime and CI execution
- planner output may use validation ids, while legacy exact command strings remain temporarily compatible
- runtime records validation ids on run steps and verifies declared expectations instead of return code alone

## Consequences

Positive:

- validation steps become easier to inspect, reason about, and reuse
- runtime and CI still share one tracked source of truth while gaining richer semantics
- planner prompts can point to stable refs instead of brittle full command strings

Tradeoffs:

- the validation config schema becomes more complex than a plain command list
- backward compatibility needs to stay in place during the transition from raw commands to ids
- richer expectations still remain intentionally lightweight; this is not a full job-spec system

## Rejected Alternatives

- arbitrary command planning with post-hoc review: rejected because it weakens governance
- moving validation rules into CI only: rejected because runtime and CI must stay aligned
- embedding a generic task runner or workflow engine: rejected because the project still benefits from a narrow, legible local execution model

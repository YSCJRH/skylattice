# ADR 0003: Technology Radar And Guarded Direct-To-Main Promotion

## Status

Accepted

## Context

Skylattice already had an executable task-agent MVP for constrained repo work. The next requirement was to let the system absorb external technical change over time without becoming an unbounded autonomous system.

The user explicitly wanted:

- GitHub open-source as the first external technical world
- hybrid operation with weekly batch semantics and manual triggers
- repo-contained experimentation
- direct-to-main promotion when guards pass
- reversible, logged, versioned self-change

## Decision

We add a technology radar workflow as a second first-class runtime path.

Key decisions:

- GitHub API is the first discovery source.
- Radar state lives in the same local SQLite database as task runs.
- Radar writes semantic and procedural memory with explicit provenance.
- Experiments happen on `codex/radar-*` branches and only touch whitelisted tracked paths.
- Promotions may push directly to `main`, but only through a guarded gate that checks score, validation, weekly cap, freeze state, and path allowlist.
- Promotion artifacts are tracked files plus ledger and memory entries; hidden runtime mutation is not the promotion mechanism.
- Rollback is mandatory and Git-native.

## Consequences

Positive:

- Skylattice can now turn external repository signals into durable local behavior changes.
- The behavior-change surface stays Git-reviewable.
- Failure handling remains explicit through freeze mode and rollback.

Tradeoffs:

- Direct-to-main promotion is intentionally narrow and still carries more risk than a pure PR-only lane.
- The first behavior change mechanism is conservative: scoring boosts via an adoption registry, not arbitrary self-editing.
- GitHub discovery introduces token dependence for the radar path, though not for the whole runtime.

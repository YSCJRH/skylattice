# Evolution Loop

Skylattice evolves through explicit, reviewable artifacts. The technology radar is now the primary bounded evolution engine for external technical change.

## Loop

1. `observe`
   - scan GitHub open-source repositories through the radar source
   - collect repository and release evidence into local SQLite
2. `reflect`
   - score candidates against tracked topics, freshness, activity, release recency, and current capability gaps
   - write semantic memory for shortlisted candidates
3. `propose`
   - generate a repo-contained spike plan for the strongest candidates
   - limit experiments to whitelisted tracked paths
4. `sandbox`
   - create a `codex/radar-*` branch
   - write an experiment artifact under `docs/radar/experiments/`
   - run tracked validation commands
5. `evaluate`
   - check validation success, candidate score threshold, weekly promotion cap, freeze state, and path allowlist
6. `promote or rollback`
   - promote at most one candidate per run to `main`
   - record promotion metadata and update `configs/radar/adoptions.yaml`
   - support explicit rollback through stored promotion commits

## What May Change

Allowed evolution targets in the current implementation:

- semantic memory summaries
- procedural memory notes about adopted patterns
- tracked radar experiment artifacts
- tracked promotion logs
- tracked adoption registry entries that influence future scoring

Not in automatic scope:

- core runtime orchestration
- governance core logic
- database schema migration logic
- destructive git operations
- browser or arbitrary shell autonomy

## Gates

A promotion only proceeds when all of these hold:

- freeze mode is off
- candidate score meets the promotion threshold
- experiment validation passed
- weekly promotion cap has not been exceeded
- every changed path is inside `configs/radar/promotion.yaml`

If promotion failures accumulate past the tracked threshold, the radar enters freeze mode and stops promoting until explicitly recovered.

# Task Brief: Phase 5 Decision Frame

## Intent

- Lock Phase 5 to one primary outcome: operationally validate the technology-radar local scheduling and provider-neutral foundation without widening autonomy or broadening scope.
- Success means a maintainer can tell what Phase 5 is trying to prove, what counts as done, and what work is intentionally secondary or deferred.

## Constraints

- tracked artifacts to edit: `docs/tasks/phase-5-decision-frame.md`, `docs/roadmap.md`
- local-only artifacts expected to change: none
- explicit non-goals: no code changes, no release tag change, no second live radar provider in this framing step, no resident scheduler, no expansion of task-agent scope

## Affected Subsystems

- roadmap and release framing
- radar scheduling and validation story
- radar provider and identity contract messaging
- onboarding and distribution prioritization

## Verification

- manual doc consistency check against `README.md`, `docs/roadmap.md`, `docs/technology-radar.md`, `docs/radar-scheduling.md`, `docs/releases/v0-3-0.md`, and `docs/tasks/project-handover-baseline.md`
- `git diff --check`

## Notes

### Decision

- Phase 5 primary outcome: engineering closure of the radar foundation, not broad feature expansion and not growth work as the phase-defining story.
- Recommended phase story: Skylattice proves that its tracked local radar scheduling and provider-neutral contract can survive real operator use while keeping the same governance, promotion, and rollback boundaries.

### Why This Wins

- the largest current ambiguity is not whether onboarding needs work, but whether the new radar foundation has fully crossed from "implemented" to "operationally validated"
- the repo already shows strong internal delivery discipline, while external demand signal is still thin; making growth or second-provider expansion the phase headline would outrun the available evidence
- this framing stays consistent with Skylattice's proof-first promise and avoids widening autonomy just to create a bigger release story

### Exit Criteria

- one full weekly scheduled radar cycle has been run and validated end to end, with a local report and a first tracked weekly validation note
- tracked docs consistently describe GitHub as the only live provider in this slice and do not imply that a second provider has already shipped
- the next wedge after Phase 5 is chosen from evidence and recorded explicitly before scope broadens

### Secondary Workstreams

- onboarding clarity from issues `#2`, `#3`, and `#4` remains important, but it is a supporting lane rather than the phase-defining outcome
- external authority and discoverability work should continue as maintenance, not as the criterion for Phase 5 completion
- prompt truth-source cleanup and authenticated smoke validation remain valuable follow-ups once the radar foundation is operationally closed

### Explicit Deferrals

- second live radar provider
- resident scheduler or daemon
- AST-aware task edits
- broad hosted or autonomous platform positioning

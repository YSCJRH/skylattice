# Task Brief: Phase 5 Decision Frame

## Intent

- Lock the next release cycle to one primary outcome: Phase 5 operational closure around the technology-radar local scheduling and provider-neutral foundation.
- Success means a maintainer can tell what the next release is trying to prove, which four exit criteria gate the release, and which work remains explicitly secondary or deferred.

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

- manual doc consistency check against `README.md`, `docs/roadmap.md`, `docs/technology-radar.md`, `docs/radar-scheduling.md`, `docs/github-workflow.md`, `docs/releases/v0-3-0.md`, and `docs/tasks/project-handover-baseline.md`
- `git diff --check`

## Notes

### Decision

- Next release primary outcome: engineering closure of the radar foundation, not broad feature expansion and not growth work as the release-defining story.
- Recommended phase story: Skylattice proves that its tracked local radar scheduling and provider-neutral contract can survive repeatable operator use while keeping the same governance, promotion, and rollback boundaries.

### Why This Wins

- the largest current ambiguity is not whether onboarding needs work, but whether the new radar foundation has fully crossed from "implemented" to "operationally validated"
- the repo already shows strong internal delivery discipline, while external demand signal is still thin; making growth or second-provider expansion the phase headline would outrun the available evidence
- this framing stays consistent with Skylattice's proof-first promise and avoids widening autonomy just to create a bigger release story

### Exit Criteria

- a second tracked weekly validation note records a follow-up operator pass after the 2026-04-16 baseline record, now captured in `docs/ops/radar-validations/2026-04-17-weekly-github.md`
- the radar scheduling runbook distinguishes safe validation mode from the live promotion-capable path, including prerequisites, working-directory expectations, and known limits
- tracked prompt files under `prompts/system/` own the human-readable planner and editor instructions, while runtime code keeps interpolation, schemas, parsing, and enforcement only
- the release-validation chain is recorded honestly: required checks pass, and auth-dependent checks are marked skipped or blocked when credentials are unavailable instead of being treated as passed

### Secondary Workstreams

- onboarding clarity from issues `#2`, `#3`, and `#4` remains important, but it is a supporting lane rather than the phase-defining outcome
- external authority and discoverability work should continue as maintenance, not as the criterion for Phase 5 completion
- GitHub issue and PR re-triage remains a release check once local auth is available, not a phase gate

### Current Closure Read

- the current release-defining story remains engineering closure around repeatable safe weekly validation, prompt truth-source alignment, and honest auth-dependent verification
- issues `#2`, `#3`, and `#4` stay open as onboarding and wording signal, not as Phase 5 closeout gates
- the maintainer-facing closure snapshot now lives in [phase-5-operational-closure-status.md](phase-5-operational-closure-status.md)

### Explicit Deferrals

- second live radar provider
- resident scheduler or daemon
- AST-aware task edits
- broad hosted or autonomous platform positioning
- archived benchmark-branch resurrection as a release-scope item

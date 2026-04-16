# Task Brief: Project Handover Baseline

## Intent

- Capture a durable handover baseline for Skylattice as of 2026-04-16 after reviewing the tracked docs, core runtime code, tests, and public GitHub surfaces.
- Success means a new maintainer can answer what Skylattice is for, what phase it is in, what boundaries must not move, what is verified today, and what should happen next without reconstructing chat history.

## Constraints

- tracked artifacts to edit: `docs/tasks/project-handover-baseline.md`
- local-only artifacts expected to change: none
- explicit non-goals: no code changes, no roadmap rewrite, no governance widening, no reprioritization that silently changes Phase 5 scope

## Affected Subsystems

- docs and public positioning: consolidate the current product story, stable release posture, and onboarding gaps
- runtime and task-agent: capture the current execution model, recovery behavior, and orchestration hotspots
- memory and governance: preserve the local-first, review-driven boundary as a non-negotiable design constraint
- radar and Phase 5: capture the current frontier around schedule validation, provider abstraction, and provider-neutral identity
- GitHub workflow and distribution: record the current release cadence, Pages posture, and early external feedback loop

## Verification

- docs reviewed: `README.md`, `docs/overview.md`, `docs/use-cases.md`, `docs/comparison.md`, `docs/architecture.md`, `docs/governance.md`, `docs/memory-model.md`, `docs/technology-radar.md`, `docs/github-workflow.md`, `docs/roadmap.md`, `docs/ai-distribution-ops.md`, `docs/releases/v0-3-0.md`, `CHANGELOG.md`, and ADRs `0011` through `0016`
- code reviewed: `src/skylattice/cli.py`, `src/skylattice/runtime/service.py`, `src/skylattice/planning/service.py`, `src/skylattice/radar/service.py`, plus the main test surfaces in `tests/test_smoke.py`, `tests/test_memory.py`, `tests/test_radar.py`, and `tests/test_public_readiness.py`
- remote checks reviewed: `gh repo view`, `gh release list`, `gh issue list`, `gh pr list`, `gh run list`, and local `git log`
- runtime checks run on 2026-04-16: `python -m skylattice.cli doctor`, `python -m compileall src/skylattice`, and `python -m pytest -q` with `63 passed in 153.91s`
- manual checks: `git status --short --branch` showed `main...origin/main` with a clean worktree before this brief, and remote release, issue, pull request, and workflow state matched the local release story in `README.md`, `CHANGELOG.md`, and `docs/roadmap.md`

## Notes

### Snapshot

- product position: early-stage but stable public baseline; proof-first, governance-heavy, and local-first
- best current framing: a reference-quality minimal product for inspectable agent behavior, not a broad hosted agent platform
- current phase: `v0.3.0 Stable` published on 2026-04-15 closed Phase 4 and opened Phase 5
- external maturity: strong internal delivery discipline, weak external traction so far

### Boundaries To Preserve

- GitHub remains a collaboration and audit layer, not runtime truth
- `.local/` remains private runtime state and must never become tracked memory
- there is still no resident scheduler or hidden background worker in the current architecture
- there is still no silent widening of `repo-write`, `external-write`, `destructive-repo-write`, or `self-modify`
- radar promotion remains constrained to the tracked allowlist and rollbackable Git paths

### Current Risks

- Phase 5 still lacks a full weekly-cycle validation story and a second live radar provider
- runtime prompt truth is split between tracked prompt files and Python code
- `TaskAgentService` and `RadarService` are concentrated orchestration hotspots
- most integration confidence still comes from fake adapters rather than authenticated end-to-end checks
- external feedback and onboarding signal are still thinner than the internal roadmap signal

### Priority Queue

1. `P0` Lock the Phase 5 decision frame.
   Outcome: decide whether the next release is primarily about engineering closure, onboarding clarity, or external validation. Deliverables: one short decision note plus updated issue and roadmap framing. Done when Phase 5 has one primary outcome and two to three explicit exit criteria.
2. `P0` Build the handover maps that the repo still lacks.
   Outcome: create durable maps for execution flow, truth sources, write permissions, and test coverage. Deliverables: one operator-facing architecture map or a small set of follow-up docs under `docs/tasks/`. Done when a new maintainer can locate where behavior lives without reading the whole repo.
3. `P1` Close the real weekly radar validation loop.
   Outcome: run at least one real scheduled radar cycle, export the local validation report, and convert it into the tracked weekly note path the docs already suggest. Deliverables: the first tracked validation record under `docs/ops/radar-validations/` plus any runbook fixes. Done when schedule intent, run provenance, and weekly review evidence all line up in practice.
4. `P1` Remove prompt truth-source drift.
   Outcome: choose whether planner and system prompts are loaded from tracked prompt files or intentionally owned in runtime code. Deliverables: a task brief, then either code alignment or doc correction. Done when one place is clearly the truth source and the other is derivative or removed.
5. `P1` Turn the current open issues into a real onboarding feedback loop.
   Outcome: use issues `#2`, `#3`, and `#4` to collect first-run friction and convert it into ranked docs and product fixes. Deliverables: a feedback summary and targeted updates to `README.md`, `docs/use-cases.md`, `docs/comparison.md`, or `docs/quickstart.md`. Done when the top three friction points are resolved, documented, or explicitly deferred.
6. `P2` Raise confidence in real external integrations.
   Outcome: add an opt-in authenticated validation lane for the GitHub and OpenAI adapters without widening autonomy. Deliverables: a narrow smoke script or documented operator check path. Done when there is at least one repeatable non-fake validation path beyond unit contracts.
7. `P2` Reassess the next capability wedge only after the above.
   Outcome: compare a second radar provider, AST-aware edits, better onboarding, and distribution work using evidence instead of intuition. Deliverables: a decision memo that ties the next wedge to real operator or visitor signal. Done when `v0.4.x` scope is explicit and bounded.

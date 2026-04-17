# Task Brief: Mainline Refresh 2026-04-17

## Intent

- Capture the current `main` line after branch cleanup and archive work on 2026-04-17.
- Success means a maintainer can answer what changed since the 2026-04-16 handover baseline, which Phase 5 facts are now true on `main`, and what should happen next without reconstructing branch history.

## Constraints

- tracked artifacts to edit: `docs/tasks/mainline-refresh-2026-04-17.md`, `docs/roadmap.md`, `docs/tasks/project-handover-baseline.md`
- local-only artifacts expected to change: none
- explicit non-goals: no code changes, no governance changes, no roadmap expansion beyond aligning current tracked facts and next-step framing

## Affected Subsystems

- docs and handover surfaces: refresh the maintainer-facing story after branch cleanup
- radar and Phase 5: align roadmap language with the tracked weekly validation record now present on `main`
- repository hygiene: capture the branch archive and single-mainline posture as durable context

## Verification

- reviewed current branch state with `git status --short --branch`, `git branch -vv`, `git branch --all`, and `git remote show origin`
- reviewed recent mainline history with `git log --graph --decorate --oneline --max-count=20 main origin/main`
- confirmed local archive tag with `git show-ref --verify refs/tags/archive/chatgpt-search-benchmark-2026-04-17`
- reviewed tracked context in `docs/roadmap.md`, `docs/tasks/project-handover-baseline.md`, `docs/ops/radar-validations/2026-04-16-weekly-github.md`, and `docs/tasks/chatgpt-search-benchmark-archive.md`
- doc verification to run after edits: `git diff --check`, `python -m mkdocs build --strict`

## Notes

### Snapshot

- `main` is clean and synced with `origin/main`
- `origin` now exposes only the `main` branch
- latest mainline commit on 2026-04-17 is `4ab5f9c` with `docs: archive chatgpt benchmark branch context`
- the archived local tag `archive/chatgpt-search-benchmark-2026-04-17` preserves the old benchmark branch tip without keeping that branch alive on the active mainline

### What Changed Since The 2026-04-16 Baseline

- the old benchmark branch is now explicitly archived instead of remaining as ambient branch context
- the first tracked weekly radar validation record is present under `docs/ops/radar-validations/`
- authenticated adapter smoke validation now exists as tracked tooling and no longer belongs in the same bucket as purely future validation ideas
- the mainline story is more cohesive: Phase 5 closure, onboarding feedback, authenticated smoke, and branch hygiene now all land on `main`

### Current Mainline Judgment

- Skylattice still reads as a governance-heavy, local-first reference runtime rather than a broad agent platform
- the current mainline emphasis is operational closure, handover clarity, and branch/document hygiene, not capability sprawl
- the next important move is no longer "create the first weekly validation record"; it is to operationalize and repeat that validation loop in a less isolated operator setting

### Current Risks

- `TaskAgentService` and `RadarService` remain orchestration hotspots
- repeatable weekly validation still depends on a credentialed operator environment even after the runbook and tracked note path are in place
- authenticated smoke now exists, but real credentialed operator validation is still opt-in and likely narrow
- external product signal is still lighter than internal delivery signal

### Priority Queue

1. `P0` Convert the first weekly validation record into a repeatable operator loop.
   Outcome: prove that the weekly radar validation path works as a repeatable practice, not only as an isolated tracked record. Deliverables: updated runbook language, one follow-up validation pass, and explicit notes about what still requires a real operator machine or real credentials.
2. `P0` Lock the post-Phase-5 decision frame.
   Outcome: decide whether the next release centers on engineering closure, onboarding clarity, or external validation. Deliverables: one short decision note plus updated roadmap framing with explicit exit criteria.
3. `P1` Turn onboarding findings into a ranked product loop.
   Outcome: convert the recent onboarding docs and feedback synthesis into a small set of visible, prioritized user-facing improvements.
4. `P2` Reassess the next capability wedge only after the above.
   Outcome: evaluate a second radar provider, better task ergonomics, or broader distribution only after operational proof and maintainer clarity are both stronger.

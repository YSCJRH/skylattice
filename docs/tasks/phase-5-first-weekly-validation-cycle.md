# Task Brief: Phase 5 First Weekly Validation Cycle

## Intent

- Execute the first end-to-end weekly radar validation cycle through the tracked `weekly-github` schedule path and promote the result into a tracked weekly validation note.
- Success means Skylattice has one concrete, reviewable record showing that `radar schedule run` and `radar schedule validate` align with the tracked schedule contract in practice.

## Constraints

- tracked artifacts to edit: `docs/tasks/phase-5-first-weekly-validation-cycle.md`, `docs/ops/radar-validations/<date>-weekly-github.md`
- local-only artifacts expected to change: `.local/work/**`, `.local/radar/validations/**`
- explicit non-goals: no resident scheduler setup, no second live provider, no runtime code changes, no remote GitHub push from the validation environment

## Affected Subsystems

- radar schedule execution and validation flow
- local clone or mirror setup used to keep the validation run isolated
- tracked weekly validation record under `docs/ops/radar-validations/`
- operator-facing schedule documentation and decision framing if the first run exposes drift

## Verification

- create an isolated clean validation repo rooted in `.local/work/`
- run `python -m skylattice.cli radar schedule run --schedule weekly-github`
- run `python -m skylattice.cli radar schedule validate --schedule weekly-github`
- confirm the validation report marks the run as valid
- confirm the tracked weekly note accurately reflects the local report and any observed promotions or failures
- run `git diff --check`
- run `python -m pytest tests/test_public_readiness.py -q`

## Notes

- the validation environment should preserve the tracked `weekly-github` schedule semantics while preventing promotion pushes from touching the primary repo or GitHub remote
- if the first live run reveals operator drift or an unexpected promotion path, capture that honestly in the weekly note instead of normalizing it away

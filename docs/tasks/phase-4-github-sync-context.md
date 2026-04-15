# Phase 4 Brief: GitHub Sync Context And Issue Preflight

## Intent

- Improve task-agent GitHub synchronization behavior without widening autonomy.
- Success means the planner can see a bounded snapshot of recent GitHub issues and pull requests when GitHub is configured, and issue-comment sync preflights the target issue before writing remotely.

## Constraints

- Tracked artifacts to edit:
  - `src/skylattice/actions/github.py`
  - `src/skylattice/runtime/service.py`
  - `src/skylattice/providers/`
  - `README.md`
  - `docs/architecture.md`
  - `docs/github-workflow.md`
  - relevant ADRs and tests
- Local-only artifacts expected to change:
  - `.local/state/skylattice.sqlite3`
  - transient test caches
- Explicit non-goals:
  - no review-thread automation
  - no automatic issue creation heuristics
  - no background GitHub sync worker
  - no GitHub dependency for no-token local runs

## Affected Subsystems

- runtime
- actions
- planning
- GitHub collaboration surfaces

## Verification

- tests for planner repo context including bounded GitHub sync context when a GitHub adapter is configured
- tests for issue-comment preflight refusing closed issues before comment sync
- `python -m pytest -q`
- `python -m compileall src/skylattice`

## Notes

- GitHub context should remain bounded and read-only, for example a small list of recent open issues and open PRs.
- Preflight should stay in the `observe` tier; the actual comment write remains `external-write`.
- This slice should help the planner avoid stale issue references without making GitHub a runtime truth dependency.

# Phase 4 Brief: Non-Destructive Repo Ops Primitives

## Intent

- Extend task-agent repo operations beyond text edits with explicit non-destructive file primitives.
- Success means task plans can declare `create_file` and `copy_file` as first-class, inspectable operations instead of overloading rewrites for every new tracked artifact.

## Constraints

- Tracked artifacts to edit:
  - `src/skylattice/actions/repo.py`
  - `src/skylattice/runtime/service.py`
  - `src/skylattice/planning/`
  - `src/skylattice/providers/`
  - `README.md`
  - `docs/architecture.md`
  - `docs/governance.md`
  - relevant ADRs and tests
- Local-only artifacts expected to change:
  - `.local/state/skylattice.sqlite3`
  - transient test output
- Explicit non-goals:
  - no delete or move primitives yet
  - no arbitrary binary-file handling
  - no widening of approval tiers
  - no AST-aware code transforms

## Affected Subsystems

- actions
- runtime
- planning
- governance

## Verification

- workspace tests for `create_file` and `copy_file`
- task-run tests that inspect materialized payloads for new repo-op steps
- `python -m pytest -q`
- `python -m compileall src/skylattice`

## Notes

- This slice intentionally prefers non-destructive primitives because current governance treats destructive requests as deny-by-default.
- `create_file` should fail if the destination already exists.
- `copy_file` should only copy tracked-safe text files and should fail if the destination already exists.

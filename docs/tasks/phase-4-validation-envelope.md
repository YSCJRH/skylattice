# Phase 4 Brief: Tracked Validation Envelope

## Intent

- Narrow the next Phase 4 slice to safer command execution envelopes and richer verification for task-agent validation steps.
- Success means validation no longer relies on raw command strings alone: each tracked check has a stable ID, declared expectations, and profile membership, while runtime, CLI, and CI continue sharing one tracked source of truth.

## Constraints

- Tracked artifacts to edit:
  - `configs/task/validation.yaml`
  - `src/skylattice/runtime/task_config.py`
  - `src/skylattice/runtime/service.py`
  - `src/skylattice/actions/repo.py`
  - `src/skylattice/planning/`
  - `src/skylattice/providers/`
  - `tools/run_validation_suite.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/governance.md`
  - relevant ADRs and tests
- Local-only artifacts expected to change:
  - `.local/state/skylattice.sqlite3`
  - transient test caches and build output
- Explicit non-goals:
  - no arbitrary shell command support
  - no background validation scheduler
  - no change to approval tiers
  - no widening of task-agent write permissions

## Affected Subsystems

- runtime
- planning
- actions
- governance
- public engineering baseline

## Verification

- tests for loading the richer tracked validation config
- tests for resolving validation IDs to tracked commands
- tests for stdout/stderr or return-code expectations on validation steps
- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`

## Notes

- This slice should stay compatible with the existing Windows-first baseline.
- The runtime and CI should still read the same tracked config, even if the schema becomes richer.
- Planner output may remain conservative at first; returning validation IDs is preferred, but compatibility with existing exact command strings can be preserved during the transition.

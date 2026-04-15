# Task Brief: Phase 5 Schedule Validation Report

## Intent

Turn the weekly scheduled radar validation loop into a repeatable local operation by adding a CLI surface that checks a radar run against tracked schedule intent and writes a local validation report artifact.

## Success Criteria

- `skylattice radar schedule validate` can validate a specific radar run or the latest radar run
- the validation output compares tracked schedule intent with recorded run provenance
- the default report path lives under `.local/` and is never promoted to tracked repo state automatically
- the schedule runbook explains how to use the validation report after a scheduled run
- tests cover the report payload and default local export path

## Affected Subsystems

- radar schedule CLI in `src/skylattice/cli.py`
- radar service validation/report logic in `src/skylattice/radar/service.py`
- README and radar scheduling docs
- radar and public-readiness tests

## Tracked Artifacts To Edit

- `src/skylattice/cli.py`
- `src/skylattice/radar/service.py`
- `README.md`
- `docs/radar-scheduling.md`
- `docs/roadmap.md`
- `tests/test_radar.py`
- `tests/test_public_readiness.py`

## Local-Only Artifacts Expected To Change

- `.local/radar/validations/`
- `.local/state/skylattice.sqlite3`
- transient docs build and test outputs

## Verification

- `python -m pytest tests/test_radar.py -q`
- `python -m pytest tests/test_public_readiness.py -q`
- `python tools/run_validation_suite.py`
- `python -m mkdocs build --strict`
- `python -m skylattice.cli radar schedule validate --schedule weekly-github`

## Non-Goals

- no resident scheduler
- no automatic promotion of validation reports into tracked docs
- no second live provider

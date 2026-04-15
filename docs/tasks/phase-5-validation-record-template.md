# Task Brief: Phase 5 Weekly Validation Record Template

## Intent

Bridge the gap between local weekly schedule validation artifacts and tracked reviewable records by adding a repository template plus explicit suggested record paths in the validation output.

## Success Criteria

- `radar schedule validate` returns the tracked template path and a suggested tracked record destination
- a tracked template exists for weekly radar validation notes without automatically writing into tracked docs
- the radar scheduling runbook explains how to convert a local `.local/` validation report into a tracked weekly record
- tests cover the suggested path and template metadata

## Affected Subsystems

- radar schedule validation output in `src/skylattice/radar/service.py`
- radar scheduling docs and tracked template artifacts
- public-readiness and radar tests

## Tracked Artifacts To Edit

- `src/skylattice/radar/service.py`
- `docs/radar-scheduling.md`
- `docs/ops/radar-weekly-validation-template.md`
- `docs/tasks/phase-5-validation-record-template.md`
- `README.md`
- `tests/test_radar.py`
- `tests/test_public_readiness.py`

## Local-Only Artifacts Expected To Change

- `.local/radar/validations/`
- transient docs build and test outputs

## Verification

- `python -m pytest tests/test_radar.py -q`
- `python -m pytest tests/test_public_readiness.py -q`
- `python tools/run_validation_suite.py`
- `python -m mkdocs build --strict`

## Non-Goals

- no automatic writing into tracked `docs/`
- no resident scheduler
- no second live provider

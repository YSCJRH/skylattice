# Task Brief: Phase 5 Scheduled Radar Provenance

## Intent

Make scheduled radar runs explicitly inspectable by recording their tracked schedule provenance in the radar run model, serialized inspect surfaces, and operator docs.

## Success Criteria

- `skylattice radar schedule run` records which schedule triggered the run
- radar run inspection exposes `trigger_mode` and `schedule_id`
- run digests and operator-facing docs make scheduled-vs-direct scans visibly different
- the Windows scheduling runbook explains how to confirm the recorded provenance after a scheduled execution
- tests cover the new provenance fields without changing existing experiment or promotion behavior

## Affected Subsystems

- radar run model and repository persistence
- runtime database schema migration for radar run provenance fields
- radar scan and schedule execution flow
- radar inspect serialization
- README, roadmap, and radar scheduling docs
- radar and public-readiness tests

## Tracked Artifacts To Edit

- `src/skylattice/radar/models.py`
- `src/skylattice/radar/repositories.py`
- `src/skylattice/runtime/db.py`
- `src/skylattice/radar/service.py`
- `README.md`
- `docs/radar-scheduling.md`
- `docs/roadmap.md`
- `tests/test_radar.py`
- `tests/test_public_readiness.py`

## Local-Only Artifacts Expected To Change

- `.local/state/skylattice.sqlite3` if local schedule commands are run
- transient test and docs build outputs

## Verification

- `python -m pytest tests/test_radar.py -q`
- `python -m pytest tests/test_public_readiness.py -q`
- `python tools/run_validation_suite.py`

## Non-Goals

- no resident scheduler
- no weekly waiting loop inside the repo
- no second live provider

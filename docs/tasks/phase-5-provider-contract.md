# Task Brief: Phase 5 Provider Contract

## Intent

Prepare the radar workflow for a future second provider without introducing a second live source yet. The immediate goal is to move provider selection out of hardcoded runtime assumptions and into tracked configuration that keeps provider provenance explicit.

## Success Criteria

- radar provider selection is driven by tracked config rather than assuming GitHub whenever a GitHub adapter exists
- the tracked config can describe multiple providers, even though only GitHub is enabled in this slice
- `doctor` and radar state snapshots expose the configured default provider plus enabled provider ids
- the runtime still uses GitHub as the only live provider in this slice
- docs and tests explain that this is a contract-preparation step, not a multi-provider rollout

## Affected Subsystems

- radar config loading in `src/skylattice/radar/config.py`
- radar source resolution in `src/skylattice/radar/service.py`
- task-agent doctor and radar state reporting in `src/skylattice/runtime/service.py`
- operator-facing docs in `README.md`, `docs/technology-radar.md`, `docs/architecture.md`, and `docs/roadmap.md`
- radar and public-readiness tests

## Tracked Artifacts To Edit

- `configs/radar/providers.yaml`
- `src/skylattice/radar/config.py`
- `src/skylattice/radar/service.py`
- `src/skylattice/runtime/service.py`
- `README.md`
- `docs/technology-radar.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `tests/test_radar.py`
- `tests/test_public_readiness.py`

## Local-Only Artifacts Expected To Change

- `.local/state/skylattice.sqlite3` if operator-facing commands are run locally
- transient test and docs build output

## Verification

- `python -m pytest tests/test_radar.py -q`
- `python -m pytest tests/test_public_readiness.py -q`
- `python tools/run_validation_suite.py`

## Non-Goals

- no second live radar provider
- no browser scraping or hosted aggregation
- no widening of experiment, promotion, or approval semantics

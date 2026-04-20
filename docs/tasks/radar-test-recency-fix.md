# Task Brief: Radar Test Recency Fix

## Intent

- Restore the radar test suite to a deterministic green state by removing wall-clock-sensitive candidate timestamps from the fake radar source fixtures.
- Success means `tests/test_radar.py` no longer depends on specific calendar dates for a candidate to clear the promotion threshold.

## Constraints

- tracked artifacts to edit: `docs/tasks/radar-test-recency-fix.md`, `tests/test_radar.py`
- local-only artifacts expected to change: none
- explicit non-goals: no runtime scoring change, no promotion-threshold change, no radar workflow behavior change outside tests

## Affected Subsystems

- radar test fixtures
- radar scoring regression coverage

## Verification

- `python -m pytest tests/test_radar.py -q`
- `python -m pytest -q`
- `python tools/run_validation_suite.py`

## Notes

- use timestamps relative to the current clock inside the fake radar source fixture so the intended promote/experiment split stays stable over time

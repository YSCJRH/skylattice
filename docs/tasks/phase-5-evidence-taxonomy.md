# Task Brief: Phase 5 Normalized Radar Evidence Taxonomy

## Intent

Normalize radar evidence kinds into a provider-neutral taxonomy so future providers can emit inspectable evidence without reusing GitHub-shaped labels.

## Success Criteria

- radar evidence kinds use a stable provider-neutral vocabulary
- legacy GitHub-shaped evidence labels remain readable through compatibility normalization
- inspect surfaces show normalized evidence kinds
- GitHub radar source emits the normalized kinds directly
- docs and tests explain the taxonomy without implying a second live provider is already enabled

## Affected Subsystems

- radar evidence models and repository deserialization
- GitHub radar source evidence emission
- radar inspect serialization and docs
- radar and public-readiness tests

## Tracked Artifacts To Edit

- `src/skylattice/radar/models.py`
- `src/skylattice/radar/repositories.py`
- `src/skylattice/radar/source.py`
- `docs/technology-radar.md`
- `docs/architecture.md`
- `docs/adrs/0016-normalized-radar-evidence-taxonomy.md`
- `tests/test_radar.py`
- `tests/test_public_readiness.py`

## Local-Only Artifacts Expected To Change

- transient test and docs build outputs

## Verification

- `python -m pytest tests/test_radar.py -q`
- `python -m pytest tests/test_public_readiness.py -q`
- `python tools/run_validation_suite.py`
- `python -m mkdocs build --strict`

## Non-Goals

- no second live provider
- no scoring or promotion threshold changes
- no removal of provider-specific payload details inside evidence payloads

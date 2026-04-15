# Task Brief: Phase 5 Provider-Neutral Adoption Matching

## Intent

Move radar adoption matching and scoring boosts off a GitHub-only `repo_slug` assumption and onto the provider-neutral identity contract introduced in Phase 5, while keeping existing adoption records compatible.

## Success Criteria

- adoption registry entries can carry `source_provider`, `source_kind`, `source_handle`, and `source_url`
- scoring boost prefers provider-neutral identity matching and falls back to legacy `repo_slug`
- promotion writes the richer identity fields into `configs/radar/adoptions.yaml`
- existing GitHub-origin adoption behavior remains compatible
- docs and tests explain the new matching rule without claiming a second live provider exists

## Affected Subsystems

- radar adoption record config loading in `src/skylattice/radar/config.py`
- radar scoring in `src/skylattice/radar/scoring.py`
- radar promotion registry writes in `src/skylattice/radar/service.py`
- roadmap and radar docs
- radar and public-readiness tests

## Tracked Artifacts To Edit

- `src/skylattice/radar/config.py`
- `src/skylattice/radar/scoring.py`
- `src/skylattice/radar/service.py`
- `README.md`
- `docs/technology-radar.md`
- `docs/roadmap.md`
- `docs/adrs/0015-provider-neutral-adoption-matching.md`
- `tests/test_radar.py`
- `tests/test_public_readiness.py`

## Local-Only Artifacts Expected To Change

- `.local/state/skylattice.sqlite3` if local radar checks run
- transient test and docs build outputs

## Verification

- `python -m pytest tests/test_radar.py -q`
- `python -m pytest tests/test_public_readiness.py -q`
- `python tools/run_validation_suite.py`
- `python -m mkdocs build --strict`

## Non-Goals

- no second live radar provider
- no changes to promotion thresholds or approval boundaries
- no removal of legacy `repo_slug` fields in this slice

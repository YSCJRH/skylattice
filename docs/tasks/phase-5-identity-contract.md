# Task Brief: Phase 5 Provider-Neutral Radar Identity Contract

## Intent

Reduce the remaining GitHub-specific assumptions in radar candidate and evidence surfaces by introducing a provider-neutral identity contract, while keeping GitHub as the only live source.

## Success Criteria

- radar candidates expose a stable provider-neutral identity shape in addition to the existing GitHub-oriented fields
- radar evidence exposes provider object type, id, and canonical URL as explicit fields instead of hiding them inside ad hoc payloads
- GitHub radar source populates those identity fields consistently
- inspect surfaces and operator-facing text use the normalized identity where it improves future-provider compatibility
- docs and tests explain that this is a contract-hardening slice, not a second live provider rollout

## Affected Subsystems

- radar models and repository persistence
- runtime database schema migration for radar evidence identity fields
- GitHub radar source candidate and evidence construction
- radar inspect serialization and experiment/promotion text surfaces
- architecture and radar docs
- radar and public-readiness tests

## Tracked Artifacts To Edit

- `src/skylattice/radar/models.py`
- `src/skylattice/radar/repositories.py`
- `src/skylattice/runtime/db.py`
- `src/skylattice/radar/source.py`
- `src/skylattice/radar/service.py`
- `docs/technology-radar.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `README.md`
- `tests/test_radar.py`
- `tests/test_public_readiness.py`

## Local-Only Artifacts Expected To Change

- `.local/state/skylattice.sqlite3` if local doctor or radar checks run
- transient test and docs build outputs

## Verification

- `python -m pytest tests/test_radar.py -q`
- `python -m pytest tests/test_public_readiness.py -q`
- `python tools/run_validation_suite.py`
- `python -m mkdocs build --strict`

## Non-Goals

- no second live radar provider
- no changes to promotion thresholds or approval semantics
- no removal of existing GitHub-specific fields yet; this slice only adds the normalized contract beside them

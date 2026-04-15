## Intent

Close out Skylattice Phase 4 by hardening GitHub collaboration sync, then open Phase 5 with a tracked local scheduling foundation and radar source abstraction.

## Success Criteria

- task-agent records branch-scoped pull-request preflight state before PR sync
- pull-request sync results expose reusable remote-target metadata for inspect, status, and recovery
- recovery guidance distinguishes draft-PR create/update behavior from issue-comment dedupe behavior
- radar gains tracked schedule config plus `skylattice radar schedule ...` CLI read/run surfaces
- radar discovery depends on a stable source interface instead of a concrete GitHub-only type
- radar evidence and candidate metadata persist provider identity without breaking existing local SQLite state
- docs, roadmap, ADRs, and release surfaces align on `v0.3.0 Stable`

## Affected Subsystems

- `src/skylattice/actions/github.py`
- `src/skylattice/runtime/*`
- `src/skylattice/radar/*`
- `src/skylattice/api/*`
- `src/skylattice/cli.py`
- `configs/radar/*`
- `docs/*`
- `tests/*`

## Tracked Artifacts To Edit

- `docs/tasks/phase-4-closeout-phase-5-entry.md`
- `docs/adrs/0011-github-collaboration-sync-hardening.md`
- `docs/adrs/0012-local-scheduler-and-radar-source-abstraction.md`
- `docs/roadmap.md`
- `docs/github-workflow.md`
- `docs/technology-radar.md`
- `docs/releases/*`
- `README.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `mkdocs.yml`
- `CITATION.cff`
- `configs/radar/schedule.yaml`
- `src/skylattice/actions/github.py`
- `src/skylattice/runtime/service.py`
- `src/skylattice/runtime/db.py`
- `src/skylattice/radar/config.py`
- `src/skylattice/radar/models.py`
- `src/skylattice/radar/source.py`
- `src/skylattice/radar/service.py`
- `src/skylattice/radar/repositories.py`
- `src/skylattice/cli.py`
- `src/skylattice/api/app.py`
- `tests/test_smoke.py`
- `tests/test_radar.py`
- `tests/test_public_readiness.py`

## Local-Only Artifacts Expected To Change

- `.local/state/skylattice.sqlite3`
- `.local/memory/exports/*` if memory export commands are exercised manually
- `.local/site/` or `site/` if docs are built locally

## Verification Steps

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- `python -m mkdocs build --strict`
- targeted manual checks for:
  - `skylattice radar schedule show`
  - `skylattice radar schedule render --target windows-task`
  - `task inspect` / `task status` recovery summaries exposing remote target metadata

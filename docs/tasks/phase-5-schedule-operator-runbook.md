# Task Brief: Phase 5 Schedule Operator Runbook

## Intent

Tighten the Phase 5 radar scheduling slice so the tracked schedule surface is not only inspectable, but also directly usable by a Windows operator without hidden working-directory assumptions.

## Success Criteria

- `skylattice radar schedule render --target windows-task` emits registration details that keep the scheduled task anchored to the repository root.
- The rendered payload includes the commands an operator needs to register, inspect, trigger, and remove the task without inventing undocumented shell glue.
- The repo documents a Windows-first operator runbook for schedule registration, first run, and weekly-cycle validation.
- Tests cover the richer render payload and verify that the registration command includes the repo working directory.

## Affected Subsystems

- radar schedule rendering in `src/skylattice/radar/service.py`
- CLI-facing schedule output consumed through `src/skylattice/cli.py`
- Phase 5 operator docs in `README.md`, `docs/technology-radar.md`, and a new schedule runbook page
- radar tests and docs build verification

## Tracked Artifacts To Edit

- `src/skylattice/radar/service.py`
- `tests/test_radar.py`
- `README.md`
- `docs/technology-radar.md`
- `docs/roadmap.md`
- `mkdocs.yml`
- `docs/radar-scheduling.md`

## Local-Only Artifacts Expected To Change

- `.local/state/skylattice.sqlite3` may update if local CLI checks run
- transient MkDocs build output under `site/`

## Verification

- `python -m pytest tests/test_radar.py -q`
- `python -m mkdocs build --strict`
- manual sanity check of `python -m skylattice.cli radar schedule render --target windows-task`

## Non-Goals

- no resident scheduler or background daemon
- no second live radar provider
- no automatic OS task registration from within Skylattice

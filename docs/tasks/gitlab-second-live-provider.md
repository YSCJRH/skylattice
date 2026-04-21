# Task Brief: GitLab Second Live Radar Provider

## Intent

- add GitLab as the second live radar provider in a bounded read-only rollout
- prove that Skylattice's provider-neutral radar architecture is operational beyond GitHub without widening promotion semantics, autonomy, or scheduler scope

## Constraints

- tracked artifacts to edit: `docs/tasks/gitlab-second-live-provider.md`, `docs/adrs/0017-gitlab-second-live-provider.md`, `src/skylattice/actions/`, `src/skylattice/radar/`, `src/skylattice/runtime/service.py`, `tools/run_authenticated_smoke.py`, `configs/radar/providers.yaml`, selected docs under `README.md` and `docs/`, and radar/public-readiness tests
- local-only artifacts expected to change: `.local/state/skylattice.sqlite3` if operator diagnostics are run locally
- explicit non-goals: no multi-source aggregation, no task-agent GitLab sync, no self-managed GitLab generalization, no resident scheduler, no AST-aware task edits, no promotion-rule widening

## Affected Subsystems

- GitLab read-only adapter surface
- radar source resolution and enrichment
- auth diagnostics and authenticated smoke guidance
- provider rollout docs and radar/public-readiness tests

## Verification

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- `python tools/run_validation_suite.py`
- `python -m mkdocs build --strict`
- `git diff --check`

## Notes

- first slice targets `gitlab.com` only and keeps `github` as the default radar provider in tracked config
- `GITLAB_TOKEN` stays explicit in the first live slice; no CLI bridge helper is needed for GitLab in this task
- the implementation should reuse the existing provider-neutral candidate, evidence, and adoption surfaces instead of inventing a GitLab-only radar contract

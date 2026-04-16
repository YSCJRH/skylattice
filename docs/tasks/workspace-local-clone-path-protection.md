# Task Brief: Workspace Local Clone Path Protection

## Intent

- Fix the workspace path-protection check so a repository cloned under `.local/work/` is still treated as a normal repo root, while paths inside that repo's own `.local/` subtree remain protected.
- Success means isolated validation clones can exercise tracked radar writes without being rejected purely because an ancestor directory is named `.local`.

## Constraints

- tracked artifacts to edit: `docs/tasks/workspace-local-clone-path-protection.md`, `src/skylattice/actions/repo.py`, `tests/test_smoke.py`
- local-only artifacts expected to change: none
- explicit non-goals: no change to the policy that repo-internal `.local/` paths are protected, no governance widening, no radar behavior change

## Affected Subsystems

- repository workspace path resolution and file listing
- isolated validation clone workflows
- workspace regression tests

## Verification

- `python -m pytest tests/test_smoke.py -q`
- `python -m compileall src/skylattice`
- `git diff --check`

## Notes

- this bug was exposed by the first weekly radar validation cycle, where a clone rooted under `.local/work/` could not write `docs/radar/experiments/...` because the adapter inspected absolute path parts instead of repo-relative path parts

# Post-Release Polish Brief

## Intent

- clean up documentation that still reads like the public preview has not shipped yet
- align README, release notes, overview, contributing guidance, and public-surface tests with the current remote GitHub state

## Constraints

- tracked artifacts to edit:
  - `README.md`
  - `CHANGELOG.md`
  - `CONTRIBUTING.md`
  - `docs/overview.md`
  - `docs/releases/v0.2.0-public-preview.md`
  - `docs/tasks/post-release-polish.md`
  - `tests/test_public_readiness.py`
- local-only artifacts expected to change:
  - none
- explicit non-goals:
  - no runtime changes
  - no CI workflow changes
  - no release asset generation

## Affected Subsystems

- docs
- public positioning
- contribution guidance
- public-surface regression checks

## Verification

- `python -m pytest tests/test_public_readiness.py -q`
- manual review for stale phrases such as `draft`, `once published`, and `next public steps` in the edited files

## Notes

- assume the remote repository description, topics, PR merge, and `v0.2.0` pre-release are already live
- keep the edits narrowly scoped to post-release consistency
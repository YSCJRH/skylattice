# Task Brief: Web Preview Proof Validation Lane

## Intent

- make the hosted app preview proof-data check part of the normal maintainer validation path instead of leaving it as a manual-only helper
- success means CI, maintainer checklists, and review guidance all treat `web-app-preview-state.json` validation as a first-class public-surface check

## Constraints

- tracked artifacts to edit:
  - `.github/workflows/ci.yml`
  - `.github/PULL_REQUEST_TEMPLATE.md`
  - `README.md`
  - `docs/github-workflow.md`
  - `tests/test_public_readiness.py`
- local-only artifacts expected to change:
  - none
- explicit non-goals:
  - no runtime behavior changes
  - no widening of tracked task validation policy in `configs/task/validation.yaml`
  - no new preview product surface

## Affected Subsystems

- GitHub Actions CI
- maintainer validation workflow
- public preview proof-data maintenance

## Verification

- `python tools/check_web_preview_state.py`
- `python -m pytest tests/test_public_readiness.py -q`
- `python -m mkdocs build --strict`
- manual checks:
  - CI file includes the preview proof-data check
  - README public-readiness checklist mentions the same command
  - PR template and GitHub workflow docs describe the check consistently

## Notes

- assumption: preview proof data is now a durable public-facing artifact and should fail fast when it drifts
- risk: keep this check separate from the tracked runtime validation profile so the runtime baseline does not silently expand into web-product-only concerns
- follow-up: if the preview surface grows more complex, a dedicated preview validation job could split from the main Windows lane later

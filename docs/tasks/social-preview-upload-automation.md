# Social Preview Upload Automation

## Intent

- turn the final GitHub social preview upload step into a repeatable local automation
- success means an operator can validate and upload `docs/assets/social-preview.png` without manually navigating GitHub settings

## Constraints

- tracked artifacts to edit: `tools/upload_github_social_preview.py`, `pyproject.toml`, `docs/ai-distribution-ops.md`, `README.md`, tests
- local-only artifacts expected to change: `.local/browser/github-social-preview/**`
- explicit non-goals: no secret storage in Git, no CI-triggered upload, no broad GitHub settings automation beyond social preview upload

## Affected Subsystems

- docs
- public surfaces
- discoverability
- GitHub workflow

## Verification

- `python tools/upload_github_social_preview.py --check-only`
- `python -m pytest tests/test_public_readiness.py tests/test_social_preview_upload_tool.py -q`
- `python -m mkdocs build --strict`

## Notes

- GitHub exposes social preview uploads through repository settings UI, not as a public REST field
- the automation uses Playwright and a private browser profile under `.local/`

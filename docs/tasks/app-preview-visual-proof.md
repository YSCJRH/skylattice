# Task Brief: App Preview Visual Proof

## Intent

- give the hosted app preview path a public-safe visual proof asset so first-time evaluators can understand the product surface before running it locally
- success means the docs site shows a representative, clearly labeled app preview snapshot on public pages without implying a hosted live deployment exists

## Constraints

- tracked artifacts to edit:
  - `docs/assets/*`
  - `docs/app-preview.md`
  - `docs/proof.md`
  - `README.md`
  - `tests/test_public_readiness.py`
- local-only artifacts expected to change:
  - none
- explicit non-goals:
  - no screenshot automation pipeline
  - no hosted app deployment claim
  - no runtime or preview behavior changes

## Affected Subsystems

- public proof surfaces
- app preview discoverability
- visual product positioning

## Verification

- `python -m pytest tests/test_public_readiness.py -q`
- `python -m mkdocs build --strict`
- manual checks:
  - the new asset renders in the docs site
  - the surrounding copy labels it as representative preview output
  - the docs do not imply the app is already publicly hosted

## Notes

- assumption: a public-safe SVG snapshot is the lowest-friction way to expose the app shape before a real hosted URL exists
- risk: avoid making the snapshot look like a live telemetry screenshot; it should remain obviously representative
- follow-up: once a public hosted app exists, this SVG can be replaced or complemented by real captured screenshots

# Task Brief: App Preview Entry Page

## Intent

- make the hosted app preview path discoverable from the public docs site instead of relying on README-only discovery
- success means first-time visitors can land on one public docs page, understand what `npm run web:preview` does, know which app routes are worth opening first, and understand that the preview is read-only

## Constraints

- tracked artifacts to edit:
  - `docs/*.md`
  - `mkdocs.yml`
  - `README.md`
  - `tests/test_public_readiness.py`
- local-only artifacts expected to change:
  - none
- explicit non-goals:
  - no hosted deployment work
  - no runtime or auth boundary changes
  - no new app behavior beyond documentation and discoverability

## Affected Subsystems

- public Pages docs
- public product positioning
- web preview discoverability

## Verification

- `python -m pytest tests/test_public_readiness.py -q`
- `python -m mkdocs build --strict`
- manual check:
  - the new page is reachable from docs navigation
  - the page clearly labels the preview as read-only
  - the page points to `npm run web:preview` as the simplest first-look path

## Notes

- assumption: the local preview remains the truthful first product-shaped entry until a public hosted app URL exists
- risk: avoid writing the page like a deployment announcement; it should stay honest about local-only scope
- follow-up: once a real hosted app URL exists, this page can become the bridge from “preview locally” to “open the public app”

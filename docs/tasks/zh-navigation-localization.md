# Task Brief: Chinese Navigation Localization

## Intent

- localize the public docs navigation and entry labels when visitors are on `/zh/` pages
- success means Chinese pages no longer expose the main docs entry points only in English, while English pages keep their current labels

## Constraints

- tracked artifacts to edit:
  - `overrides/main.html`
  - `tests/test_public_readiness.py`
  - optional docs/task brief updates
- local-only artifacts expected to change:
  - none
- explicit non-goals:
  - no full rewrite of all Chinese page content in this task
  - no separate MkDocs build or new i18n plugin
  - no changes to runtime or app preview behavior

## Affected Subsystems

- GitHub Pages docs theme override
- Chinese public docs discoverability and first-run UX

## Verification

- `python -m pytest tests/test_public_readiness.py -q`
- `python -m mkdocs build --strict`
- manual checks:
  - `/zh/` pages render navigation labels in Chinese
  - English pages keep the existing English labels

## Notes

- assumption: the smallest safe fix is a theme override that only rewrites labels on `/zh/` pages at render time
- risk: old Chinese content pages may still contain separate encoding/content issues after this navigation fix
- follow-up: repair the older garbled Chinese page bodies in a separate, content-focused pass

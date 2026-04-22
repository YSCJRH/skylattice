# Task Brief: Chinese App Preview Mirror

## Intent

- add a Chinese public mirror for the hosted app preview entry so the bilingual docs surface stays consistent
- success means Chinese-speaking visitors can discover, understand, and follow the read-only app preview path from the Pages site without falling back to the English-only page

## Constraints

- tracked artifacts to edit:
  - `docs/app-preview.md`
  - `docs/zh/*.md`
  - `mkdocs.yml`
  - `docs/llms-full.txt`
  - `docs/sitemap.xml`
  - `tests/test_public_readiness.py`
- local-only artifacts expected to change:
  - none
- explicit non-goals:
  - no runtime or preview behavior changes
  - no full Chinese translation pass for every app-specific page

## Affected Subsystems

- bilingual public docs
- discoverability metadata
- public app preview positioning

## Verification

- `python -m pytest tests/test_public_readiness.py -q`
- `python -m mkdocs build --strict`
- manual checks:
  - the new Chinese page is reachable from the Chinese nav
  - alternates and sitemap point to the Chinese mirror
  - the page clearly labels the preview as read-only and local-first

## Notes

- assumption: the app preview page is now important enough to deserve the same bilingual treatment as other public entry surfaces
- risk: avoid overpromising a hosted product in translation; keep the same boundary language as the English page
- follow-up: if the app preview page evolves further, keep the Chinese mirror updated in the same task instead of letting it drift

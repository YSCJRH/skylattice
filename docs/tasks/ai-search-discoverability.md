## Intent

- make Skylattice easier for search engines and AI answer systems to crawl, understand, cite, and recommend
- succeed when the repository gains a GitHub Pages distribution layer, machine-readable discovery files, query-aligned public pages, and a repeatable benchmark for AI-search visibility

## Constraints

- tracked artifacts to edit: `README.md`, `CONTRIBUTING.md`, `pyproject.toml`, `.github/workflows/*`, `docs/**`, `tests/test_public_readiness.py`, and new Pages config files
- local-only artifacts expected to change: local virtualenv caches and MkDocs build output under `site/` during verification
- explicit non-goals: change runtime behavior, broaden autonomy, convert `v0.2.0` from pre-release to stable, or make GitHub Pages the runtime truth source

## Affected Subsystems

- governance and public positioning
- GitHub workflow and Pages distribution
- docs and release surfaces
- public-readiness validation

## Verification

- run `python -m pytest -q`
- run `python -m compileall src/skylattice`
- run `python -m skylattice.cli doctor`
- run `python tools/run_validation_suite.py`
- run `python -m mkdocs build --strict`
- confirm the Pages build contains `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt`, bilingual core pages, and the custom social preview asset

## Notes

- GitHub remains the code and collaboration source of truth; Pages is a distribution layer
- English root pages are canonical and Chinese pages live under `docs/zh/`
- `llms.txt` is treated as an auxiliary discovery signal rather than a primary ranking mechanism
- GitHub `homepageUrl` and custom social preview still need remote settings aligned after the branch is published

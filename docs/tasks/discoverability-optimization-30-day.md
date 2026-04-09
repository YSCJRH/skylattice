# 30-Day Discoverability Optimization

## Intent

- improve non-brand discoverability for Skylattice through clearer public pages, stronger version signals, and prepared external authority assets
- succeed when the Chinese mirror is readable, the core Pages surfaces answer search-shaped questions directly, and the repository is ready for a stable non-pre-release release plus weekly discoverability reviews

## Constraints

- tracked artifacts to edit: `README.md`, `mkdocs.yml`, `pyproject.toml`, `CITATION.cff`, `CHANGELOG.md`, `docs/**`, `evals/ai-search/**`, `tests/test_public_readiness.py`
- local-only artifacts expected to change: temporary build output under `site/`, any local verification caches under `.local/`
- explicit non-goals: do not widen runtime autonomy, do not add hosted services, do not commit `.local/` evidence, and do not rely on live ChatGPT web automation for acceptance

## Affected Subsystems

- kernel: none
- memory: none
- actions: none
- planning: none
- governance: public positioning only, no policy widening
- evolution: none
- ledger: none
- public distribution: GitHub Pages, release surfaces, AI-search review loop, outreach assets

## Verification

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- `python tools/run_validation_suite.py`
- `$env:NO_MKDOCS_2_WARNING='true'; python -m mkdocs build --strict`
- manual doc consistency check for English and Chinese Pages entry points, release links, and sitemap/llms alignment

## Notes

- assumptions: English remains canonical, Chinese remains under `/zh/`, and the next public version should expose a conventional latest-release signal
- risks: Chinese encoding regressions, stale release references, and drift between tracked docs and remote GitHub metadata
- follow-up tasks: publish the stable GitHub release, upload the social preview image if needed, and complete Search Console / Bing verification

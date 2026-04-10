# External Authority Program

## Intent

- turn the current discoverability assets into a practical 30-day authority program that can earn legitimate mentions, backlinks, and community discussions
- succeed when Skylattice has execution-grade launch posts, short-form community copy, directory blurbs, a posting runbook, and a tracked post-release review baseline

## Constraints

- tracked artifacts to edit: `README.md`, `mkdocs.yml`, `docs/outreach/**`, `docs/ai-distribution-ops.md`, `evals/ai-search/**`, `tests/test_public_readiness.py`
- local-only artifacts expected to change: none beyond normal build output under `site/`
- explicit non-goals: do not spam irrelevant communities, do not fabricate testimonials, do not widen runtime behavior, and do not commit private outreach notes

## Affected Subsystems

- kernel: none
- memory: none
- actions: none
- planning: none
- governance: none
- evolution: none
- ledger: none
- public distribution: launch copy, directory blurbs, posting cadence, and post-release review summaries

## Verification

- `python -m pytest tests/test_public_readiness.py -q`
- `$env:NO_MKDOCS_2_WARNING='true'; python -m mkdocs build --strict`
- manual review of English and Chinese outreach assets for clean UTF-8 text and backlink alignment

## Notes

- assumptions: `v0.2.1 Stable` remains the canonical release signal during this outreach window
- risks: overposting to low-fit communities, fragmented messaging across English and Chinese surfaces, and stale link targets
- follow-up tasks: execute the runbook, record real posting dates, and run a Day 14 discoverability review against the post-release baseline

# Radar Sample

This walkthrough shows what a successful, public-safe technology radar run looks like when Skylattice discovers a promising open-source project and promotes a bounded pattern back into tracked repository state.

## Scenario

Window:

> weekly

Setup:

- radar source: repository fake radar source
- discovered candidate: `example/radar-kit`
- validation command: `python -m pytest -q`
- promotion target: tracked radar experiment and promotion paths only

## What Happens

1. Skylattice discovers a candidate through the radar source.
2. The candidate is enriched, scored, and marked `promote`.
3. A bounded experiment branch is created under `codex/radar-*`.
4. The experiment writes reviewable docs and config changes, then validates them.
5. Promotion metadata is recorded, including rollback target and main commit.
6. Semantic, procedural, and episodic memory are refreshed from the run.

## What To Look For In The JSON

Open [radar-run-sample.json](radar-run-sample.json) and check for these signals:

- `run.status` is `completed`
- the top candidate has a score and a `promote` decision
- experiment output points at `docs/radar/experiments/...`
- promotion metadata includes `rollback_target`
- memory includes semantic, procedural, and episodic records tied to the run
- evidence shows why the candidate entered the radar pipeline

## Why This Matters

The sample demonstrates the second half of Skylattice's thesis: bounded self-improvement should be inspectable, reviewable, and reversible. The runtime learns through tracked artifacts and promotion logs instead of hidden model drift.

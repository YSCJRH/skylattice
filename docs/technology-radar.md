# Technology Radar

The technology radar is Skylattice's bounded external-learning workflow.

## Goal

Turn GitHub open-source change into durable, reviewable local capability through this path:

`discovery -> scoring -> knowledge increment -> experiment -> promotion -> rollback`

## Sources

Current live source set:

- GitHub repository search
- GitHub repository metadata
- GitHub latest release metadata

No webpage scraping, browser automation, or multi-source aggregation is in scope yet.
The runtime now expresses this through a stable `RadarDiscoverySource` boundary so future providers can fit without rewriting `RadarService`.
Tracked provider intent now lives in `configs/radar/providers.yaml`, so future provider rollout starts as a reviewable config change instead of a hidden runtime assumption.
Candidate and evidence inspection now also carries a provider-neutral identity contract beside the current GitHub-shaped fields, so future providers do not need to masquerade as GitHub repositories just to enter the radar pipeline.

## Candidate Selection

Tracked source config lives in:

- `configs/radar/providers.yaml`
- `configs/radar/sources.yaml`
- `configs/radar/scoring.yaml`
- `configs/radar/promotion.yaml`
- `configs/radar/schedule.yaml`

The current defaults favor:

- recent repositories
- recently active repositories
- strong star signal
- topic overlap with `agent`, `memory`, `evals`, `developer-tools`, `coding-agent`, `openai`, and `github`

## Experiment Shape

Each spike is repo-contained and intentionally narrow.

Artifacts:

- experiment branch: `codex/radar-<slug>-<runid>`
- experiment note: `docs/radar/experiments/<slug>-<runid>.md`
- promotion log: `docs/radar/promotions/<slug>-<runid>.md`
- behavior change registry: `configs/radar/adoptions.yaml`

## Local Scheduling

Skylattice does not run a resident scheduler inside the repo.

- tracked schedule intent lives in `configs/radar/schedule.yaml`
- `skylattice radar schedule show` exposes the tracked schedule view
- `skylattice radar schedule render --target windows-task` renders Windows-first local registration details
- `skylattice radar schedule run` resolves one tracked schedule into the same bounded `radar scan` path
- [radar-scheduling.md](radar-scheduling.md) is the operator runbook for Windows task registration, first-run checks, and weekly-cycle validation

This keeps schedule behavior reviewable without promoting GitHub or an internal queue to runtime truth.

## Promotion Rules

A candidate can promote only when:

- the worktree is clean
- the base branch is `main`
- the experiment passed validation
- the candidate cleared the promotion threshold
- the weekly promotion cap has not been exceeded
- all changed paths are inside the tracked allowlist
- freeze mode is off

## Behavior Change Mechanism

The first behavior change is deliberately simple and auditable:

- promotion writes a tracked adoption entry
- future radar scans read that adoption registry
- candidates matching adopted tags receive a small scoring boost

That means the system changes future behavior through Git-reviewed config, not hidden heuristics.

## Rollback

Each promotion stores:

- `promotion_id`
- `source_branch`
- `base_commit`
- `experiment_commit`
- `main_commit`
- `rollback_target`

Rollback is explicit and Git-native. It reverts the promotion commit chain and records the rollback in ledger and episodic memory.

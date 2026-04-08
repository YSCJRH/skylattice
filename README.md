# Skylattice

Skylattice is a private, evolvable personal agent foundation for a single user.

The repository now has two executable workflows:

- a `task-agent` path for constrained repo work and GitHub triage
- a `technology radar` path for scanning GitHub open-source projects, validating adoption spikes, and promoting bounded behavior changes back into the repo

## Product Shape

Skylattice is not a generic chatbot. It is designed to be:

- persistent in identity and mission
- local-first in runtime and memory
- Git-native in auditability
- explicit in governance and approvals
- evolvable through reversible artifacts instead of hidden state

## Current Capability

The runtime now supports two vertical slices.

Task agent:

- `CLI -> planner -> governance -> repo actions -> git push -> GitHub sync -> memory + ledger`

Technology radar:

- `GitHub discovery -> scoring -> semantic memory -> repo-contained spike -> guarded promotion -> rollback`

Implemented now:

- persistent task runs and radar runs in `.local/state/skylattice.sqlite3`
- CLI commands for `doctor`, `task ...`, and `radar ...`
- read-only API endpoints for run, memory, event, radar candidate, promotion, and digest inspection
- append-only ledger events for task and radar workflows
- SQLite-backed memory storage across working, episodic, semantic, and procedural layers
- run-scoped approvals for task execution and internal gates for radar experiment/promotion writes
- OpenAI-backed planner and file rewrite provider for task runs
- GitHub API discovery for the radar workflow when `GITHUB_TOKEN` is present
- adoption registry updates under `configs/radar/adoptions.yaml` that feed future radar scoring

## Current Limits

Skylattice is still intentionally constrained.

- radar discovery only looks at GitHub repositories and release metadata
- automatic promotion is limited to whitelisted tracked paths such as `docs/radar/**` and `configs/radar/**`
- task runs still focus on docs, ADRs, and small text-heavy repo changes
- the system does not merge PRs, rebase branches, browse the web, or widen permissions on its own

## Repository Map

Tracked surface:

- `docs/`: architecture, governance, memory model, roadmap, radar design, ADRs
- `configs/`: tracked defaults, governance baselines, and radar scoring/promotion policy
- `prompts/`: versioned core prompts and reflection templates
- `skills/`: tracked skill definitions and conventions
- `evals/`: scenario specs and redacted reports
- `src/`: runtime code, adapters, providers, radar services, repositories
- `tests/`: smoke and radar coverage

Local-only surface:

- `.local/state/`: runtime SQLite database and local snapshots
- `.local/memory/`: future local memory artifacts and indexes
- `.local/work/`: temporary work products and sandboxes
- `.local/logs/`: run logs and diagnostics
- `.local/overrides/`: local config overlays that must never be committed

Publishable root:

- the publishable root is this repository root: `D:\skylattice`
- do not commit `.local/**`, exported personal memory, or transient logs

## Quick Start

Install locally:

```bash
python -m pip install -e .
```

Inspect runtime health:

```bash
skylattice doctor
python -m uvicorn skylattice.api.app:app --reload
python -m pytest -q
```

Run a task:

```bash
skylattice task run --goal "Refresh README and prepare a draft PR"
skylattice task resume <run-id> --allow repo-write --allow external-write
skylattice task inspect <run-id>
```

Run the technology radar:

```bash
skylattice radar scan --window weekly --limit 20
skylattice radar inspect <radar-run-id-or-candidate-id>
skylattice radar rollback <promotion-id>
```

## Required Environment

Task agent path:

- `OPENAI_API_KEY`: required for planning and file rewrite generation
- `GITHUB_TOKEN`: required for GitHub draft PR and issue comment writes

Technology radar path:

- `GITHUB_TOKEN`: required for GitHub repository discovery
- `SKYLATTICE_GITHUB_REPOSITORY`: optional for task GitHub writes; radar discovery does not depend on it semantically, but the current adapter still uses the tracked repo slug as its local hint

## GitHub Remote

GitHub remote:

- repository: [YSCJRH/skylattice](https://github.com/YSCJRH/skylattice)
- role: external audit and collaboration ledger
- limit: never treat GitHub as the sole memory store

## Development Conventions

- prefer branch names like `codex/<topic>`
- prefer commit prefixes like `docs:`, `arch:`, `kernel:`, `memory:`, `gov:`, `radar:`, `eval:`
- any architecture boundary change must update docs and, when durable, add an ADR
- keep public examples redacted and sanitized

## Current Runtime Interfaces

CLI write surface:

- `skylattice doctor`
- `skylattice task run --goal <text-or-file> [--allow repo-write] [--allow external-write]`
- `skylattice task status <run-id>`
- `skylattice task resume <run-id> [--allow repo-write] [--allow external-write]`
- `skylattice task inspect <run-id>`
- `skylattice radar scan [--window weekly|manual] [--limit N]`
- `skylattice radar status <radar-run-id>`
- `skylattice radar inspect <radar-run-id|candidate-id>`
- `skylattice radar replay <candidate-id>`
- `skylattice radar rollback <promotion-id>`

Read-only API surface:

- `GET /health`
- `GET /kernel/summary`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/events`
- `GET /runs/{run_id}/memory`
- `GET /radar/runs/{run_id}`
- `GET /radar/candidates/{candidate_id}`
- `GET /radar/promotions/{promotion_id}`
- `GET /radar/digest/latest`

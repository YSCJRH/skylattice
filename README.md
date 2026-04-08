# Skylattice

Skylattice is a local-first, Git-native foundation for a persistent personal agent.

It currently exposes two bounded workflows:

- a `task-agent` path for constrained repo work and GitHub triage
- a `technology radar` path for scanning GitHub open-source projects, validating adoption spikes, and promoting bounded behavior changes back into the repo

## Product Shape

Skylattice is not a generic chatbot. It is designed to be:

- persistent in identity and mission
- durable in memory and audit history
- explicit in governance and approval boundaries
- evolvable through reversible artifacts instead of hidden state
- private-memory-by-default, with local state kept outside tracked Git history

## Implemented Today

- persistent task runs and radar runs in `.local/state/skylattice.sqlite3`
- CLI commands for `doctor`, `task ...`, and `radar ...`
- read-only API endpoints for run, memory, event, radar candidate, promotion, and digest inspection
- append-only ledger events for task and radar workflows
- SQLite-backed memory storage across working, episodic, semantic, and procedural layers
- run-scoped approvals for task execution and internal gates for radar experiment and promotion writes
- OpenAI-backed planning and file rewrite providers for task runs
- GitHub repository discovery for the radar workflow when `GITHUB_TOKEN` is present
- adoption registry updates under `configs/radar/adoptions.yaml` that feed future radar scoring

## Current Limits

- radar discovery only looks at GitHub repositories and release metadata
- automatic promotion is limited to whitelisted tracked paths such as `docs/radar/**` and `configs/radar/**`
- task runs still focus on docs, ADRs, prompts, configs, and small text-heavy repo changes
- the system does not merge PRs, rebase branches, widen permissions on its own, or export private memory by default

## Documentation Map

- `docs/blueprint-v0.1.md`: product framing and system direction
- `docs/architecture.md`: runtime modules and data flow
- `docs/governance.md`: approval model, budgets, freeze mode, and safety gates
- `docs/memory-model.md`: memory layers, write triggers, and rollback rules
- `docs/technology-radar.md`: radar workflow, scoring, promotion gates, and rollback
- `docs/roadmap.md`: staged delivery plan
- `docs/adrs/`: architecture decision records

## Repository Layout

Tracked surface:

- `docs/`: architecture, governance, memory model, roadmap, radar design, and ADRs
- `configs/`: tracked defaults, governance baselines, and radar scoring and promotion policy
- `prompts/`: versioned core prompts and reflection templates
- `skills/`: tracked skill definitions and conventions
- `evals/`: scenario specs and redacted reports
- `src/`: runtime code, adapters, providers, radar services, and repositories
- `tests/`: smoke, radar, and publishability coverage

Local-only surface:

- `.local/state/`: runtime SQLite database and local snapshots
- `.local/memory/`: local memory artifacts and indexes
- `.local/work/`: temporary work products and sandboxes
- `.local/logs/`: run logs and diagnostics
- `.local/overrides/`: local config overlays that must never be committed

Publishable root:

- the publishable root is the repository root
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

## Runtime Interfaces

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

## Environment

Task agent path:

- `OPENAI_API_KEY`: required for planning and file rewrite generation
- `GITHUB_TOKEN`: required for GitHub draft PR and issue comment writes
- `SKYLATTICE_GITHUB_REPOSITORY`: optional by default and expected to be set locally when you want task GitHub writes enabled

Technology radar path:

- `GITHUB_TOKEN`: required for GitHub repository discovery
- `SKYLATTICE_GITHUB_REPOSITORY`: optional for promotion logs or task-linked GitHub writes; tracked defaults do not bind the runtime to a personal repo

## Publication Posture

- tracked defaults use neutral placeholder identities and `UTC`
- GitHub write targets are not hard-coded into tracked config
- personal runtime state stays under `.local/` and is ignored by Git
- public examples and eval artifacts should stay redacted

## Project Home

- repository: [YSCJRH/skylattice](https://github.com/YSCJRH/skylattice)
- role: remote collaboration and audit surface, not the sole memory store

## Public Readiness Checklist

- `python -m pytest -q`
- `skylattice doctor`
- run the publishability audit in `tests/test_public_readiness.py`
- `git ls-files .local`
- set a short repository description and topics before changing visibility
- keep Issues enabled
- keep Discussions disabled initially
- keep Wiki disabled initially

## Development Conventions

- prefer branch names like `codex/<topic>`
- prefer commit prefixes like `docs:`, `arch:`, `kernel:`, `memory:`, `gov:`, `radar:`, `eval:`
- any architecture boundary change must update docs and, when durable, add an ADR
- keep public examples redacted and sanitized
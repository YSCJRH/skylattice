# Skylattice

Skylattice is a private, evolvable personal agent foundation for a single user.

Version `0.1` now includes an executable task-agent MVP for repository operations and GitHub triage. The runtime is still intentionally narrow: it plans and executes one constrained task lane end to end instead of trying to be a general autonomous agent.

## Product Shape

Skylattice is not a generic chatbot. It is designed to be:

- persistent in identity and mission
- local-first in runtime and memory
- Git-native in auditability
- explicit in governance and approvals
- evolvable through reversible artifacts instead of hidden state

## Current Capability

The current vertical slice is `CLI -> planner -> governance -> repo actions -> git push -> GitHub sync -> memory + ledger`.

Implemented now:

- persistent task runs in `.local/state/skylattice.sqlite3`
- CLI commands for `doctor`, `task run`, `task status`, `task resume`, `task inspect`
- read-only API endpoints for run, event, and memory inspection
- SQLite-backed run, ledger, and memory storage
- run-scoped approvals for `repo-write` and `external-write`
- OpenAI-backed planner and file rewrite provider via the Responses API
- local repo actions for controlled file edits and whitelisted checks
- Git actions for branch, commit, and push
- direct GitHub API integration for draft PR sync and issue comments

## Current Limits

Skylattice is still intentionally constrained.

- it is optimized for repo maintenance, docs, ADRs, and small text-heavy changes
- it does not support browser automation yet
- it does not merge PRs, rebase branches, or widen permissions automatically
- it does not perform uncontrolled background autonomy

## Repository Map

Tracked surface:

- `docs/`: architecture, governance, memory model, roadmap, ADRs
- `configs/`: tracked defaults and policy baselines
- `prompts/`: versioned core prompts and reflection templates
- `skills/`: tracked skill definitions and conventions
- `evals/`: scenario specs and redacted reports
- `src/`: runtime code, adapters, providers, repositories
- `tests/`: smoke and integration coverage for the task-agent slice

Local-only surface:

- `.local/state/`: runtime SQLite database and local snapshots
- `.local/memory/`: future local memory artifacts and indexes
- `.local/work/`: temporary work products and sandboxes
- `.local/logs/`: run logs and diagnostics
- `.local/overrides/`: local config overlays that must never be committed

Publishable root:

- The publishable root is this repository root: `D:\skylattice`
- Do not commit `.local/**`, exported personal memory, or transient logs

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

## Required Environment

For the full task-agent path:

- `OPENAI_API_KEY`: required for planning and file rewrite generation
- `GITHUB_TOKEN`: required for GitHub read/write actions
- `SKYLATTICE_GITHUB_REPOSITORY`: optional override for repo slug; defaults to the tracked runtime config

If `OPENAI_API_KEY` is absent, `task run` will fail fast with a clear error and `doctor` will report `planner_available: false`.

## Bootstrap Git Flow

Skylattice is local-first and push-later:

```bash
git init -b main
git remote add origin git@github.com:YSCJRH/skylattice.git
git add .
git commit -m "docs: bootstrap skylattice v0.1 foundation"
git push -u origin main
```

HTTPS is acceptable in place of SSH if that is your local preference.

GitHub remote:

- repository: [YSCJRH/skylattice](https://github.com/YSCJRH/skylattice)
- role: external audit and collaboration ledger
- limit: never treat GitHub as the sole memory store

## Development Conventions

- prefer branch names like `codex/<topic>`
- prefer commit prefixes like `docs:`, `arch:`, `kernel:`, `memory:`, `gov:`, `eval:`
- any architecture boundary change must update docs and, when durable, add an ADR
- keep public examples redacted and sanitized

## Current Runtime Interfaces

CLI write surface:

- `skylattice doctor`
- `skylattice task run --goal <text-or-file> [--allow repo-write] [--allow external-write]`
- `skylattice task status <run-id>`
- `skylattice task resume <run-id> [--allow repo-write] [--allow external-write]`
- `skylattice task inspect <run-id>`

Read-only API surface:

- `GET /health`
- `GET /kernel/summary`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/events`
- `GET /runs/{run_id}/memory`

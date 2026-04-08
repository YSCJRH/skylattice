# Architecture

## Current Shape

Skylattice is a single-process, local-first runtime with two executable workflows sharing the same local state surface:

- `task-agent`: constrained repo work and GitHub triage
- `technology-radar`: GitHub open-source discovery, bounded experimentation, guarded promotion, and rollback

Both workflows share:

- local SQLite state in `.local/state/skylattice.sqlite3`
- append-only ledger events
- layered memory storage
- governance policy and approval logic
- repo workspace and git adapters

## Main Components

### Kernel

`src/skylattice/kernel/`

- loads tracked defaults, local overrides, and env overlays
- defines stable agent identity, user model, relationship model, mission, and runtime snapshot
- provides a durable summary surface for CLI and API inspection

### Runtime Layer

`src/skylattice/runtime/`

- `TaskAgentService` is the top-level facade used by CLI and API
- task runs and radar runs both create shadow entries in the generic `runs` table so ledger and memory can reference one shared run id surface
- `RuntimeDatabase` owns the tracked schema for task, ledger, memory, and radar tables

### Task Agent Path

`src/skylattice/planning/`, `src/skylattice/actions/`, `src/skylattice/providers/`

Flow:

1. interpret goal
2. generate constrained plan
3. gate repo and external writes
4. execute file/git/GitHub actions
5. verify results
6. write episodic and procedural memory

### Technology Radar Path

`src/skylattice/radar/`

Flow:

1. discover GitHub repositories via API
2. score candidates against tracked topics, freshness, activity, releases, and capability gaps
3. record semantic memory for shortlisted candidates
4. create repo-contained spike branches under `codex/radar-*`
5. validate spikes with tracked checks
6. promote at most one candidate per run to `main` through a guarded allowlist
7. update `configs/radar/adoptions.yaml` and promotion logs
8. support rollback through explicit promotion records

## Data Stores

### Tracked

- `configs/agent/defaults.yaml`
- `configs/policies/governance.yaml`
- `configs/radar/*.yaml`
- prompts, skills, docs, ADRs, eval specs
- `configs/radar/adoptions.yaml` as a reviewable behavior-change registry

### Local Only

- `.local/state/skylattice.sqlite3`
- `.local/memory/`
- `.local/work/`
- `.local/logs/`
- `.local/overrides/`

## Key Boundaries

- GitHub is a source and audit surface, not runtime truth.
- Radar promotions are limited to whitelisted tracked paths from `configs/radar/promotion.yaml`.
- `src/skylattice/runtime/`, `src/skylattice/governance/`, and core schema paths are intentionally outside the automatic radar promotion path.
- The runtime does not depend on GitHub to exist, but the radar workflow depends on `GITHUB_TOKEN` for discovery.

## Observability

- every task and radar run has ledger events
- memory writes are attached to run ids when applicable
- radar promotions persist `promotion_id`, `source_branch`, `base_commit`, `experiment_commit`, `main_commit`, and `rollback_target`
- `skylattice doctor` and the read-only FastAPI surface expose the current local state without enabling mutation

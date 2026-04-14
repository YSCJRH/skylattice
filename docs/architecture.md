# Architecture

![Skylattice runtime architecture](assets/runtime-architecture.svg)

Skylattice is a single-process, local-first runtime with two executable workflows sharing the same local state surface. If you want the operator-facing quick start and public-safe sample outputs first, start from [the landing page](index.md) and [proof.md](proof.md).

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
- `load_task_validation_policy()` loads tracked validation commands from `configs/task/validation.yaml`
- validation commands now carry stable ids, expected outputs, and profile membership instead of acting as a flat string allowlist
- local memory review, export, and retrieval ranking stay CLI-first; FastAPI only exposes read surfaces for record inspection and search

### Task Agent Path

`src/skylattice/planning/`, `src/skylattice/actions/`, `src/skylattice/providers/`

Flow:

1. interpret goal
2. retrieve ranked profile, procedural, and semantic memory for the current goal
3. generate a constrained plan with declared edit modes, tracked validation refs, and bounded GitHub sync context when available
4. gate repo and external writes
5. execute deterministic text edits or full rewrites through the repo workspace adapter
6. verify results with tracked validation commands and local edit invariants
7. expose retry diagnostics for blocked or halted steps, then resume only with explicit operator action
8. write episodic and procedural memory

The planner can see a bounded `memory_context`, but memory retrieval does not widen permissions or validation scope.
Resume behavior is also bounded: blocked and halted steps expose structured recovery metadata, and GitHub sync steps try to reuse prior remote artifacts instead of blindly duplicating them.
GitHub context is similarly bounded: planner prompts may see recent open issues and PRs, but GitHub remains advisory collaboration context rather than runtime truth.

Current task edit modes:

- `rewrite`
- `replace_text`
- `insert_after`
- `append_text`
- `create_file`
- `copy_file`

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
- `configs/task/validation.yaml`
- `configs/radar/*.yaml`
- prompts, skills, docs, ADRs, eval specs
- `configs/radar/adoptions.yaml` as a reviewable behavior-change registry
- `.github/workflows/ci.yml` and GitHub templates as public collaboration behavior

### Local Only

- `.local/state/skylattice.sqlite3`
- `.local/memory/`
- `.local/work/`
- `.local/logs/`
- `.local/overrides/`

## Key Boundaries

- GitHub is a source and audit surface, not runtime truth.
- Task-agent validation commands are constrained to tracked config, profile membership, and declared expectations; they do not grant arbitrary shell execution.
- Current richer repo ops remain non-destructive: `create_file` and `copy_file` are in scope, while delete and move stay deferred.
- halted repo and external write steps remain operator-resumed; there is no automatic retry worker
- profile updates, semantic compaction, and procedural dedup stay review-driven local actions; there is no background memory mutation
- Radar promotions are limited to whitelisted tracked paths from `configs/radar/promotion.yaml`.
- `src/skylattice/runtime/`, `src/skylattice/governance/`, and core schema paths are intentionally outside the automatic radar promotion path.
- The runtime does not depend on GitHub to exist, but the radar workflow depends on `GITHUB_TOKEN` for discovery.

## Observability

- every task and radar run has ledger events
- task edit steps record their materialized payloads for inspection
- halted and blocked task steps record retry metadata and recovery guidance for `task inspect`, CLI status, and the read-only API
- memory writes are attached to run ids when applicable
- memory records can be listed, searched, exported, rolled back, and reviewed through the CLI without exposing a write API
- radar promotions persist `promotion_id`, `source_branch`, `base_commit`, `experiment_commit`, `main_commit`, and `rollback_target`
- `skylattice doctor` and the read-only FastAPI surface expose the current local state without enabling mutation


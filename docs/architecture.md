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
- `load_radar_config()` also loads tracked radar schedule intent from `configs/radar/schedule.yaml`
- `load_radar_config()` also loads tracked radar provider intent from `configs/radar/providers.yaml`
- radar candidates and evidence now persist provider-neutral identity fields alongside current GitHub-shaped compatibility fields
- radar evidence kinds are normalized to provider-neutral taxonomy values on write and read
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
GitHub context is similarly bounded: planner prompts may see recent open issues and PRs, PR sync now performs an observe-tier preflight, and recovery summaries expose remote target state without turning GitHub into runtime truth.

Current task edit modes:

- `rewrite`
- `replace_text`
- `insert_after`
- `append_text`
- `create_file`
- `copy_file`
- `move_file`
- `delete_file`

### Technology Radar Path

`src/skylattice/radar/`

Flow:

1. discover repositories through a stable source interface
2. score candidates against tracked topics, freshness, activity, releases, and capability gaps
3. record semantic memory for shortlisted candidates
4. create repo-contained spike branches under `codex/radar-*`
5. validate spikes with tracked checks
6. promote at most one candidate per run to `main` through a guarded allowlist
7. update `configs/radar/adoptions.yaml` and promotion logs
8. support rollback through explicit promotion records

Radar now also has tracked local schedule intent, tracked provider intent, plus Windows-first schedule rendering and an operator runbook, but it still delegates actual recurring execution to the operating system instead of a resident Skylattice worker.

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

## Maintainer Maps

### Execution Map

- CLI entry: `src/skylattice/cli.py`
- read-only API entry: `src/skylattice/api/app.py`
- top-level runtime facade: `src/skylattice/runtime/service.py` via `TaskAgentService.from_repo()`
- task-agent chain: planner/provider -> workspace/git/github adapters -> validation -> ledger and memory
- radar chain: discovery source -> scoring -> experiment -> promotion or rollback -> ledger and memory
- shared state surface: SQLite tables in `.local/state/skylattice.sqlite3` plus tracked config under `configs/`

### Truth-Source Map

- tracked product and policy truth: `README.md`, `docs/*.md`, `docs/adrs/*.md`, `configs/agent/defaults.yaml`, `configs/policies/governance.yaml`, `configs/task/validation.yaml`, and `configs/radar/*.yaml`
- tracked prompt intent: `prompts/system/`
- runtime orchestration truth: `src/skylattice/runtime/`, `src/skylattice/radar/`, `src/skylattice/actions/`, and `src/skylattice/memory/`
- tracked prompt files under `prompts/system/` now own the human-readable mission, planner, editor, prompt-template, and connectivity-smoke instructions; `src/skylattice/providers/openai.py` only loads those required files, interpolates templates, checks for missing prompt assets, applies JSON-schema constraints, parses responses, and enforces edit modes in runtime code
- `prompts/system/reflector.md` remains a tracked future-facing asset until a reflection runtime path exists
- local runtime truth: `.local/state/`, `.local/memory/`, `.local/logs/`, `.local/work/`, and local radar validation exports under `.local/radar/validations/`
- remote advisory truth: GitHub PR, issue, repository, and release state can guide planning and recovery, but does not replace local runtime state

### Write-Permission Map

- `observe`: local inspection, status, read-only API access, and advisory GitHub reads
- `local-safe-write`: reversible writes under approved `.local/` roots
- `repo-write`: tracked repository edits, branch creation, and commit steps initiated by task runs
- `destructive-repo-write`: required in addition to `repo-write` for tracked `move_file` and `delete_file`
- `external-write`: push, draft PR sync, and issue-comment sync for task runs
- `radar-experiment-write`: bounded spike writes on whitelisted tracked paths
- `radar-promote-main`: bounded direct-to-`main` promotion writes on whitelisted tracked paths
- `self-modify`: policy or autonomy widening, still outside normal automatic flows

### Test-Coverage Map

- `tests/test_smoke.py`: task-agent planning, edit materialization, approval gates, recovery, GitHub sync, and CLI/API smoke paths
- `tests/test_memory.py`: memory record states, retrieval ranking, review flows, rollback, and export behavior
- `tests/test_radar.py`: radar discovery contracts, scoring, scheduling, validation reports, promotion, rollback, and provider-neutral identity behavior
- `tests/test_public_readiness.py`: public-safe tracked artifacts, release surfaces, Pages metadata, outreach files, and repo hygiene
- `tools/run_authenticated_smoke.py`: opt-in read-only validation against the live GitHub, GitLab, and OpenAI adapters when operator credentials are present
- current test strength is contract and boundary coverage; authenticated end-to-end validation against live OpenAI and GitHub remains intentionally narrower and operator-invoked

## Key Boundaries

- GitHub is a source and audit surface, not runtime truth.
- Task-agent validation commands are constrained to tracked config, profile membership, and declared expectations; they do not grant arbitrary shell execution.
- Current richer repo ops are still text-first and bounded: `create_file` and `copy_file` are routine repo-write steps, while `move_file` and `delete_file` require a separate destructive approval.
- halted repo and external write steps remain operator-resumed; there is no automatic retry worker
- profile updates, semantic compaction, and procedural dedup stay review-driven local actions; there is no background memory mutation
- Radar promotions are limited to whitelisted tracked paths from `configs/radar/promotion.yaml`.
- `src/skylattice/runtime/`, `src/skylattice/governance/`, and core schema paths are intentionally outside the automatic radar promotion path.
- The runtime does not depend on GitHub or GitLab to exist, but live radar discovery depends on explicit provider credentials such as `GITHUB_TOKEN` or `GITLAB_TOKEN`.

## Observability

- every task and radar run has ledger events
- task edit steps record their materialized payloads for inspection
- halted and blocked task steps record retry metadata and recovery guidance for `task inspect`, CLI status, and the read-only API
- memory writes are attached to run ids when applicable
- memory records can be listed, searched, exported, rolled back, and reviewed through the CLI without exposing a write API
- radar promotions persist `promotion_id`, `source_branch`, `base_commit`, `experiment_commit`, `main_commit`, and `rollback_target`
- `skylattice doctor` and the read-only FastAPI surface expose the current local state without enabling mutation


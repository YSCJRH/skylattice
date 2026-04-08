# Roadmap

## Phase 0: Foundation Docs And Skeleton

Status: complete

Delivered:

- repository structure
- architecture and governance docs
- FastAPI and CLI smoke stubs

## Phase 1: Executable Task-Agent MVP

Status: complete

Delivered:

- persistent task runs in SQLite
- append-only ledger events
- SQLite-backed memory repository for working, episodic, and procedural layers
- run-scoped approval and resume flow
- OpenAI-backed plan and file rewrite provider
- local repo, git, and GitHub adapters
- CLI-first execution path and read-only run inspection API

## Phase 2: Memory Deepening

Next goals:

- explicit profile memory editing and confirmation flow
- semantic memory CRUD plus safe compaction paths
- retrieval ranking beyond simple substring matching
- export and rollback tooling for local memory artifacts

## Phase 3: Action Expansion

Next goals:

- richer repo operations beyond full-file rewrites
- safer command execution envelopes and richer verification steps
- better GitHub issue and PR synchronization behavior
- optional browser or app adapters behind the same governance layer

## Phase 4: Planner And Recovery Hardening

Next goals:

- stronger repository context gathering before planning
- richer failure recovery and step retry policies
- resumable halted runs with better diagnostics
- more robust branch and PR reconciliation behavior

## Phase 5: Bounded Evolution

Later goals:

- evolution candidates logged as first-class runtime objects
- sandboxed prompt, skill, and playbook evaluation
- promotion and rollback workflows with explicit evidence thresholds
- no silent widening of autonomy

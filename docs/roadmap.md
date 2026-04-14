# Roadmap

## Phase 0: Foundation Docs And Skeleton

Status: complete

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

## Phase 2: Technology Radar MVP

Status: complete

Delivered:

- GitHub-backed repository discovery and release enrichment
- radar run, candidate, evidence, experiment, promotion, and local freeze state tables
- semantic and procedural memory writes for radar outcomes
- repo-contained radar spikes on `codex/radar-*` branches
- guarded direct-to-main promotion path with rollback metadata
- tracked adoption registry that feeds future scoring
- CLI and API read surfaces for radar inspection

## Phase 3: Memory And Retrieval Deepening

Status: complete

Delivered:

- explicit profile memory editing and confirmation flow
- stronger semantic compaction and retrieval ranking
- procedural playbook deduplication and review tooling
- export and rollback tooling for local memory artifacts
- task-planning memory context for profile, procedural, and semantic recall
- read-only memory inspection and search API endpoints

## Phase 4: Action Expansion And Recovery Hardening

Status: in progress

Delivered so far:

- resume-safe task recovery metadata for blocked and halted runs
- branch-scoped PR reuse and deduplicated issue-comment sync on resume
- tracked validation command ids, profiles, and richer expectation checks shared by runtime and CI
- explicit non-destructive repo ops for tracked file creation and template copying

Recommended first slice:

- harden halted-run recovery, retry safety, and GitHub sync idempotency before widening task actions further
- expose clearer recovery diagnostics through inspect, CLI, and ledger surfaces

Next goals:

- richer repo operations beyond full-file rewrites
- safer command execution envelopes and richer verification steps
- better GitHub issue and PR synchronization behavior
- stronger halted-run recovery and diagnostics

## Phase 5: Scheduler And Broader Radar Sources

Later goals:

- weekly local automation for radar scans
- optional additional external sources beyond GitHub
- richer experiment templates beyond docs/config artifacts
- no silent widening of autonomy

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

Status: complete

Delivered:

- resume-safe task recovery metadata for blocked and halted runs
- branch-scoped PR reuse and deduplicated issue-comment sync on resume
- tracked validation command ids, profiles, and richer expectation checks shared by runtime and CI
- explicit non-destructive repo ops for tracked file creation and template copying
- explicit destructive repo ops for tracked file move/delete with separate operator approval
- bounded GitHub issue and PR planning context plus issue-comment preflight checks
- observe-tier pull-request preflight before sync
- richer PR sync payloads with remote target number, URL, state, draft status, and sync mode
- recovery summaries that distinguish create-vs-update PR behavior and issue-comment dedupe state

## Phase 5: Local Scheduler Foundation And Radar Source Abstraction

Status: in progress

Delivered so far:

- tracked radar provider contract in `configs/radar/providers.yaml`
- provider-neutral radar candidate and evidence identity fields alongside GitHub-shaped compatibility fields
- provider-neutral adoption matching with legacy `repo_slug` fallback
- tracked radar schedule intent in `configs/radar/schedule.yaml`
- `skylattice radar schedule show`, `render`, and `run`
- scheduled radar runs now preserve tracked schedule provenance for later inspection
- schedule validation reports now export local weekly-cycle evidence under `.local/radar/validations/`
- the first tracked weekly validation record now lives under `docs/ops/radar-validations/2026-04-16-weekly-github.md`
- Windows-first task registration rendering instead of a resident scheduler
- a Windows-first schedule operator runbook plus working-directory-safe task action rendering
- stable `RadarDiscoverySource` protocol plus provider-tagged radar evidence
- GitHub remains the only live discovery provider in this slice

Next goals:

- operationalize the first tracked weekly validation record into a repeatable weekly review loop, including at least one follow-up operator pass beyond the isolated validation clone path
- keep GitHub as the only live provider until that repeated weekly validation loop is exercised and documented, while preserving the provider-neutral contract for future expansion
- choose and document the next post-Phase-5 wedge only after that operational proof, without widening autonomy or changing promotion semantics in the meantime

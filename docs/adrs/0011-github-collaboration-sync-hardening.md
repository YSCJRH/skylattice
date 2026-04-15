# ADR 0011: GitHub Collaboration Sync Hardening Without Remote Runtime Truth

- Status: Accepted
- Date: 2026-04-15

## Context

Phase 4 already made task runs resumable and side-effect aware, but one notable gap remained in the GitHub collaboration tail:

- draft PR sync could reuse branch-scoped pull requests, but the runtime did not observe that remote state explicitly before writing
- halted or blocked runs did not surface enough remote-target detail to tell an operator whether resume would create a new draft PR, update an existing PR, or reuse an issue comment
- GitHub issue preflight already existed, but pull-request sync still looked more write-first than inspect-first

The missing piece was not more automation. It was sharper observability and recovery guidance around the same bounded external-write surface.

## Decision

We add an observe-tier collaboration preflight and expand sync results, without turning GitHub into runtime truth.

Key decisions:

- add read-only pull-request inspection by head branch before `github.sync_pull_request`
- keep PR sync branch-scoped and create/update based on the observed remote target
- extend sync and recovery payloads with remote target kind, number, URL, state, draft status, and sync mode
- extend issue preflight to report whether the current run's dedupe comment already exists
- keep GitHub advisory: local runtime state, ledger state, and recovery state still live in the local SQLite runtime, not on GitHub

## Consequences

Positive:

- operators can see whether resume will create a draft PR or update an existing one before retrying
- issue-comment recovery becomes clearer when a previous attempt already wrote the dedupe comment remotely
- `task inspect`, `task status`, and `GET /runs/{run_id}/recovery` now expose remote collaboration state as part of the same auditable recovery surface

Tradeoffs:

- runtime and adapter contracts gain another GitHub read action plus richer result payloads
- recovery summaries now carry more remote metadata, which slightly widens the amount of collaboration context stored locally

## Rejected Alternatives

- mirror GitHub PR and issue state into local runtime truth: rejected because GitHub remains a collaboration and audit layer, not the runtime substrate
- keep PR reuse implicit inside the write step only: rejected because operators need explicit remote-target guidance before resuming external writes
- add background auto-retry for GitHub sync: rejected because the current roadmap still prefers operator-triggered resume over hidden retry workers

# GitHub Workflow

## Role Of GitHub

GitHub is the external audit and collaboration layer for Skylattice. It is not the runtime dependency and not the sole memory store.

Remote repository:

- [YSCJRH/skylattice](https://github.com/YSCJRH/skylattice)

## Current Runtime Integration

The current MVP uses direct GitHub REST API calls behind `GitHubAdapter`.

Current write operations supported:

- create issue
- add issue comment
- create draft pull request
- update an existing open pull request for the same head branch

Current read operations supported:

- repository metadata lookup
- open pull request lookup by head branch

GitHub writes happen only after governance approval for `external-write`.

## Required Environment

For direct API mode:

- `GITHUB_TOKEN`
- `SKYLATTICE_GITHUB_REPOSITORY` optional override, if you want to override the repo slug from tracked config

The runtime defaults to the tracked repository hint in `configs/agent/defaults.yaml` when the environment override is absent.

## What Belongs In GitHub

- repository docs and ADRs
- tracked prompts and skills
- code interfaces and runtime logic
- redacted eval scenarios and reports
- draft PRs and optional issue updates produced by approved task runs

## What Must Stay Local By Default

- personal memory records
- raw interaction logs
- local overrides and secrets
- sandbox outputs with private content
- runtime SQLite state and indexes

## Source Of Truth

- local repository is the working source of truth
- Git history is the durable tracked change log
- GitHub mirrors the tracked surface and enables review, sync, and remote audit

## Current Task-Agent Path

The supported GitHub path is:

1. local plan generation
2. local repo edit and validation
3. local commit
4. approved push
5. approved GitHub draft PR sync
6. optional approved issue comment

This keeps the runtime local-first while still making GitHub a meaningful external ledger.

## First Push Sequence

```bash
git init -b main
git remote add origin git@github.com:YSCJRH/skylattice.git
git add .
git commit -m "docs: bootstrap skylattice v0.1 foundation"
git push -u origin main
```

## Explicit Non-Goals Right Now

- no merge automation
- no force push
- no branch deletion
- no repo settings mutation
- no GitHub Actions dependence for runtime execution

## Future GitHub Automation

Possible later additions:

- nightly redacted eval runs in GitHub Actions
- PR checks that enforce repo hygiene
- issue templates for architecture and evolution proposals

Those additions must never require exporting private memory by default.

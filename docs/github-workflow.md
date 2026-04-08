# GitHub Workflow

GitHub is an important external ledger and discovery surface, but not the runtime substrate.

## Roles

GitHub serves three roles in the current system:

- remote audit and synchronization target for this repository
- task-agent collaboration surface for draft PRs and issue comments
- technology-radar discovery surface for scanning open-source repositories and releases

## What Stays Local

- private runtime state in `.local/`
- raw memory records
- radar evidence payloads stored in SQLite
- local overrides and credentials

## What Becomes Tracked

- docs and ADRs
- prompts and skills
- governance and radar configs
- radar experiment artifacts under `docs/radar/experiments/`
- radar promotion logs under `docs/radar/promotions/`
- radar adoption registry updates under `configs/radar/adoptions.yaml`

## Task-Agent Use Of GitHub

- push working branches
- create or update draft PRs
- add issue comments when the task plan calls for them

## Technology Radar Use Of GitHub

- search repositories via the GitHub API
- read repository metadata and latest release metadata
- optionally push promotion artifacts to `origin/main`

The radar does not scrape webpages and does not treat GitHub as its only memory store.

## Direct-To-Main Policy

For the current radar MVP, successful promotions may push directly to `main`, but only when:

- promotion gates pass
- changed paths are whitelisted
- rollback metadata is recorded
- the change is represented by tracked artifacts instead of hidden runtime mutation

This is intentionally narrow and does not authorize broader automatic codebase rewriting.

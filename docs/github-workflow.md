# GitHub Workflow

GitHub is an important external ledger and discovery surface, but not the runtime substrate.

## Roles

GitHub serves five roles in the current system:

- remote audit and synchronization target for this repository
- task-agent collaboration surface for draft PRs and issue comments
- Windows-first CI surface for the tracked task validation baseline
- GitHub Pages distribution layer for public docs, search-engine discovery, and AI-readable landing pages
- technology-radar discovery surface for scanning open-source repositories and releases

## What Stays Local

- private runtime state in `.local/`
- raw memory records
- radar evidence payloads stored in SQLite
- local overrides and credentials

## What Becomes Tracked

- docs and ADRs
- prompts and skills
- governance, task, and radar configs
- GitHub workflow and template files under `.github/`
- Pages configuration, machine-readable discovery files, and public benchmark docs
- radar experiment artifacts under `docs/radar/experiments/`
- radar promotion logs under `docs/radar/promotions/`
- radar adoption registry updates under `configs/radar/adoptions.yaml`

## Task-Agent Use Of GitHub

- push working branches
- create or update draft PRs
- add issue comments when the task plan calls for them
- present PR and Issue templates that reinforce task briefs, verification, and privacy-safe reporting

## Resume-Safe Sync

Task-agent GitHub sync is now recovery-aware.

- draft PR sync remains branch-scoped, so a resumed run updates the existing draft PR instead of creating a fresh one for the same head branch
- issue comments use a stable per-run dedupe marker so resume can reuse an already-created comment if the first attempt failed after the remote write
- `task inspect`, CLI status, and `GET /runs/{run_id}/recovery` expose whether a run is resumable, what approval is required next, and the likely side-effect risk
- this is still operator-triggered recovery, not autonomous retry logic

## CI Baseline

The current public CI lane is intentionally narrow.

- runner: `windows-latest`
- Python: `3.11`
- command source of truth: `configs/task/validation.yaml`
- execution helper: `tools/run_validation_suite.py`
- public-site build check: `python -m mkdocs build --strict`

This keeps the public automation aligned with the runtime boundary while also ensuring the Pages distribution layer stays buildable.

## GitHub Pages As A Distribution Layer

The Pages site is intentionally public-facing and read-only.

- English root pages are canonical
- Chinese mirrors live under `/zh/`
- `robots.txt`, `sitemap.xml`, `llms.txt`, and `llms-full.txt` are tracked artifacts
- the site should help search engines and AI answer systems understand the repo, not replace runtime truth

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

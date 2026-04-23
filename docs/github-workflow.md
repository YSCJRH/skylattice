# GitHub Workflow

GitHub is an important external ledger and discovery surface, but not the runtime substrate.

## Roles

GitHub serves six roles in the current system:

- remote audit and synchronization target for this repository
- task-agent collaboration surface for draft PRs and issue comments
- Windows-first CI surface for the tracked task validation baseline
- GitHub Pages distribution layer for public docs, search-engine discovery, and AI-readable landing pages
- technology-radar discovery surface for scanning open-source repositories and releases
- hosted-app identity provider for the first web control-plane login flow
- public feedback surface for Hosted Alpha onboarding, comparison, and first-run signal

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
- inspect branch-scoped PR state before PR sync
- create or update draft PRs
- inspect target issues before comment sync
- add issue comments when the task plan calls for them
- present PR and Issue templates that reinforce task briefs, verification, and privacy-safe reporting

## Resume-Safe Sync

Task-agent GitHub sync is now recovery-aware.

- draft PR sync remains branch-scoped, so a resumed run updates the existing draft PR instead of creating a fresh one for the same head branch
- PR sync now performs an observe-tier preflight read after push so `task inspect`, `task status`, and recovery output can state whether resume will create a draft PR or update an existing open PR
- issue comments use a stable per-run dedupe marker so resume can reuse an already-created comment if the first attempt failed after the remote write
- planner prompts can see a bounded snapshot of recent open issues and PRs when GitHub is configured
- issue-comment sync performs an observe-tier preflight read so closed issues are rejected before the external-write step
- `task inspect`, CLI status, and `GET /runs/{run_id}/recovery` expose whether a run is resumable, what approval is required next, the likely side-effect risk, and the current remote target state
- this is still operator-triggered recovery, not autonomous retry logic

## CI Baseline

The current public CI lane is intentionally narrow.

- runner: `windows-latest`
- Python: `3.11`
- command source of truth: `configs/task/validation.yaml`
- default shared profile: `baseline`
- execution helper: `tools/run_validation_suite.py`
- preview proof-data check: `npm run web:preview:check`
- public-site build check: `python -m mkdocs build --strict`
- hosted web-app build check: `npm run web:build`

This keeps the public automation aligned with the runtime boundary while also ensuring the Pages distribution layer stays buildable.

## Release-Facing Validation Reporting

Phase 5 closeout keeps the validation story explicit.

- the public CI lane plus `tools/run_validation_suite.py` cover the no-credential tracked runtime baseline
- `npm run web:preview:check` covers the tracked hosted-app preview proof-data sample used by the public app preview path
- `python -m skylattice.cli doctor auth` is a read-only operator preflight for live capability gaps, not a replacement for CI
- `python tools/run_authenticated_smoke.py --provider github` and `--provider openai` are opt-in read-only checks outside the public CI lane
- if a credential-dependent check is not run, record it as `skipped` or `blocked` instead of treating a green CI run as proof that the live adapter path passed
- current onboarding-feedback issues remain a supporting signal for docs and positioning work, not a release gate for Phase 5 operational closure
- issues `#2`, `#3`, and `#4` are now also explicit Hosted Alpha acceptance inputs for first-run friction, comparison clarity, and post-release onboarding feedback

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

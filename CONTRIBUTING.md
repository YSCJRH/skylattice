# Contributing

Skylattice is currently optimized for clarity, documentation quality, safe incremental evolution, and public legibility.

## Preferred Contribution Style

- keep changes small and easy to review
- create a task brief in `docs/tasks/` before non-trivial work
- update docs with code when behavior or boundaries change
- add or update an ADR for durable architecture decisions
- prefer explicit interfaces over hidden coupling
- keep public examples redacted and privacy-safe
- if you change public positioning, update the Pages site, `llms*.txt`, and the related public proof surfaces in the same task

## First Checks For New Contributors

- run `python -m skylattice.cli doctor`
- read the redacted examples under `examples/redacted/`
- use the 5-minute no-credential path in `README.md` before testing token-enabled workflows
- open the Pages site locally with `python -m mkdocs build --strict` when touching public distribution content

## Local Workflow

- branch from `main` using `codex/<topic>` when possible
- use focused commit prefixes such as `docs:`, `arch:`, `kernel:`, `memory:`, `gov:`, `radar:`, or `eval:`
- run `python tools/run_validation_suite.py` before asking for review
- run `python -m pytest -q` before asking for review
- run `python -m mkdocs build --strict` when touching Pages content, public metadata, or AI-search surfaces; if needed, set `NO_MKDOCS_2_WARNING=true` to silence the current Material migration warning
- run `skylattice doctor` when touching runtime bootstrapping, config, or governance behavior

## Safety And Privacy Rules

- never commit `.local/**`, database files, logs, or private memory exports
- do not hard-code tokens, personal paths, or machine-specific defaults into tracked files
- keep `SKYLATTICE_GITHUB_REPOSITORY` and similar environment-specific settings in local overrides or environment variables
- prefer reversible edits and additive migrations over destructive changes

## Early Feedback Is Welcome

- report first-run friction, unclear positioning, and missing proof surfaces
- prefer issues that describe what blocked understanding or trust, not only code defects
- use the early-feedback issue template for visitor or onboarding feedback

## Review Expectations

- docs-first changes are welcome
- architecture changes should explain tradeoffs, not just mechanics
- tests should cover new gates, persistence changes, and public-surface behavior when practical
- PRs should call out the task brief, validation commands, and any ADR/doc boundary changes

## Maintainer Checklist For Public Updates

- confirm `README.md`, `SECURITY.md`, this file, `.github/` templates, and the Pages site still reflect the current public posture
- run `python tools/run_validation_suite.py`
- run `python -m pytest -q`
- run `python -m mkdocs build --strict`
- run `skylattice doctor`
- confirm `git ls-files .local` is empty
- confirm repository description, topics, homepage, and social preview still match the intended positioning
- keep Issues enabled and keep Discussions and Wiki disabled initially
- keep the latest release notes, Pages proof surfaces, and README proof surfaces in sync

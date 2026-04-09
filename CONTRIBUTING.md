# Contributing

Skylattice is currently optimized for clarity, documentation quality, and safe incremental evolution.

## Preferred Contribution Style

- keep changes small and easy to review
- create a task brief in `docs/tasks/` before non-trivial work
- update docs with code when behavior or boundaries change
- add or update an ADR for durable architecture decisions
- prefer explicit interfaces over hidden coupling
- keep public examples redacted and privacy-safe

## First Checks For New Contributors

- run `python -m skylattice.cli doctor`
- read the redacted examples under `examples/redacted/`
- use the 5-minute no-credential path in `README.md` before testing token-enabled workflows

## Local Workflow

- branch from `main` using `codex/<topic>` when possible
- use focused commit prefixes such as `docs:`, `arch:`, `kernel:`, `memory:`, `gov:`, `radar:`, or `eval:`
- run `python tools/run_validation_suite.py` before asking for review
- run `python -m pytest -q` before asking for review
- run `skylattice doctor` when touching runtime bootstrapping, config, or governance behavior

## Safety And Privacy Rules

- never commit `.local/**`, database files, logs, or private memory exports
- do not hard-code tokens, personal paths, or machine-specific defaults into tracked files
- keep `SKYLATTICE_GITHUB_REPOSITORY` and similar environment-specific settings in local overrides or environment variables
- prefer reversible edits and additive migrations over destructive changes

## Early Feedback Is Welcome

- report first-run friction, unclear positioning, and missing proof surfaces
- prefer issues that describe what blocked understanding or trust, not only code defects
- use the early-feedback issue template for visitor or onboarding feedback after it is published on GitHub

## Review Expectations

- docs-first changes are welcome
- architecture changes should explain tradeoffs, not just mechanics
- tests should cover new gates, persistence changes, and public-surface behavior when practical
- PRs should call out the task brief, validation commands, and any ADR/doc boundary changes

## Maintainer Checklist Before Public Visibility

- confirm `README.md`, `SECURITY.md`, this file, and `.github/` templates still reflect the current public posture
- run `python tools/run_validation_suite.py`
- run `python -m pytest -q`
- run `skylattice doctor`
- confirm `git ls-files .local` is empty
- set repository description and topics
- keep Issues enabled and keep Discussions and Wiki disabled initially
- switch visibility only after the publishability checks pass on `main`
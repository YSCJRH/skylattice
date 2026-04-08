# Contributing

Skylattice is currently optimized for clarity, documentation quality, and safe incremental evolution.

## Preferred Contribution Style

- keep changes small and easy to review
- update docs with code when behavior or boundaries change
- add or update an ADR for durable architecture decisions
- prefer explicit interfaces over hidden coupling
- keep public examples redacted and privacy-safe

## Local Workflow

- branch from `main` using `codex/<topic>` when possible
- use focused commit prefixes such as `docs:`, `arch:`, `kernel:`, `memory:`, `gov:`, `radar:`, or `eval:`
- run `python -m pytest -q` before asking for review
- run `skylattice doctor` when touching runtime bootstrapping, config, or governance behavior

## Safety And Privacy Rules

- never commit `.local/**`, database files, logs, or private memory exports
- do not hard-code tokens, personal paths, or machine-specific defaults into tracked files
- keep `SKYLATTICE_GITHUB_REPOSITORY` and similar environment-specific settings in local overrides or environment variables
- prefer reversible edits and additive migrations over destructive changes

## Review Expectations

- docs-first changes are welcome
- architecture changes should explain tradeoffs, not just mechanics
- tests should cover new gates, persistence changes, and public-surface behavior when practical

## Maintainer Checklist Before Public Visibility

- confirm `README.md`, `SECURITY.md`, and this file still reflect the current public posture
- run `python -m pytest -q`
- run `skylattice doctor`
- confirm `git ls-files .local` is empty
- set repository description and topics
- keep Issues enabled and keep Discussions and Wiki disabled initially
- switch visibility only after the publishability checks pass on `main`
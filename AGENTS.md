# Skylattice Agent Guide

This repository is designed for Codex-first local development. Treat it as a durable system blueprint plus a thin runtime, not as a scratchpad.

## Read Order

Before changing code, read in this order:

1. `README.md`
2. `docs/architecture.md`
3. `docs/governance.md`
4. `docs/memory-model.md`
5. `docs/technology-radar.md` when touching radar behavior
6. relevant ADRs in `docs/adrs/`

## Core Rules

- The publishable root is this repository root.
- `.local/**` is private runtime state and must never be committed.
- Keep tracked artifacts legible: docs, prompts, policies, skills, evals, and code should explain system behavior without needing chat history.
- Prefer reversible changes over hidden mutation.
- Do not silently widen autonomy, permissions, or self-modification scope.
- If a change alters system boundaries, approval rules, memory semantics, radar promotion behavior, or GitHub workflow, update the relevant docs in the same task.

## Task Decomposition

For any non-trivial task, work from a brief before implementation.

Use `docs/tasks/_template.md` for multi-step work and capture:

- intent and success criteria
- affected subsystems
- tracked artifacts to edit
- local-only artifacts expected to change
- verification steps

## Architecture Hygiene

- Keep the system single-process and local-first unless an ADR says otherwise.
- Treat GitHub as an audit and collaboration layer, not as runtime truth.
- Keep memory storage dual-layered: tracked schema and policies in repo, sensitive data in `.local/`.
- New adapters belong behind stable interfaces in `src/skylattice/actions/`.
- New radar behavior must pass through `configs/radar/*`, the SQLite ledger, and a rollbackable Git path.
- Automatic promotion is constrained to whitelisted tracked paths; do not add broader self-modification without a new ADR.

## Documentation Expectations

- `README.md` explains operator-facing behavior.
- `docs/*.md` explain subsystem intent, invariants, and tradeoffs.
- `docs/adrs/*.md` capture durable architectural decisions.
- `prompts/` and `configs/` are versioned artifacts, not hidden runtime magic.
- `configs/radar/adoptions.yaml` is behavior-changing tracked state; treat edits there as architecture-relevant.

## Branches And Commits

- default branch naming: `codex/<topic>`
- commit prefix suggestions: `docs:`, `arch:`, `kernel:`, `memory:`, `gov:`, `actions:`, `radar:`, `eval:`
- group changes by decision boundary, not by editor session

## Guardrails For Coding Agents

- Never commit secrets, personal memory exports, or `.local/` contents.
- Never add vendor lock-in to the action layer without documenting the abstraction boundary first.
- Never implement self-modification that writes directly to tracked prompts or policies without a reviewable ledger path.
- Never widen radar promotion allowlists without updating `configs/radar/promotion.yaml`, `docs/governance.md`, and the latest ADR.
- Never convert Markdown-first docs into opaque generated artifacts.

## Minimum Verification

Run the lightest useful verification for the change:

- `python -m pytest` for smoke and radar coverage
- `python -m compileall src/skylattice` for import-level sanity
- targeted CLI checks such as `skylattice doctor`
- manual doc consistency check when architecture or governance changes

If verification cannot be run, say so explicitly.

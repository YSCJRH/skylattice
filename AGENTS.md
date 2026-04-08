# Skylattice Agent Guide

This repository is designed for Codex-first local development. Treat it as a durable system blueprint plus a thin runtime, not as a scratchpad.

## Read Order

Before changing code, read in this order:

1. `README.md`
2. `docs/blueprint-v0.1.md`
3. `docs/architecture.md`
4. `docs/governance.md`
5. `docs/memory-model.md`
6. relevant ADRs in `docs/adrs/`

## Core Rules

- The publishable root is this repository root.
- `.local/**` is private runtime state and must never be committed.
- Keep tracked artifacts legible: docs, prompts, policies, skills, evals, and code should explain system behavior without needing chat history.
- Prefer reversible changes over hidden mutation.
- Do not silently widen autonomy, permissions, or self-modification scope.
- If a change alters system boundaries, approval rules, memory semantics, or GitHub workflow, update the relevant docs in the same task.

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
- New memory backends must preserve rollback and export semantics.

## Documentation Expectations

- `README.md` explains operator-facing behavior.
- `docs/*.md` explain subsystem intent, invariants, and tradeoffs.
- `docs/adrs/*.md` capture durable architectural decisions.
- `prompts/` and `configs/` are versioned artifacts, not hidden runtime magic.

## Branches And Commits

- default branch naming: `codex/<topic>`
- commit prefix suggestions: `docs:`, `arch:`, `kernel:`, `memory:`, `gov:`, `actions:`, `eval:`
- group changes by decision boundary, not by editor session

## Guardrails For Coding Agents

- Never commit secrets, personal memory exports, or `.local/` contents.
- Never add vendor lock-in to the action layer without documenting the abstraction boundary first.
- Never implement self-modification that writes directly to tracked prompts or policies without a reviewable ledger path.
- Never convert Markdown-first docs into opaque generated artifacts.

## Minimum Verification

Run the lightest useful verification for the change:

- `python -m pytest` for smoke coverage
- targeted import or CLI checks for new modules
- manual doc consistency check when architecture or governance changes

If verification cannot be run, say so explicitly.

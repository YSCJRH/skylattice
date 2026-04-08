# ADR 0001: System Direction

- Status: Accepted
- Date: 2026-04-08

## Context

Skylattice needs a durable foundation for a private personal agent that can evolve over time without losing legibility, governance, or local ownership.

## Decision

We will build Skylattice as:

- a single-user system
- a local-first runtime
- a Git-native repository of prompts, policies, docs, skills, and evals
- a Python codebase with a thin FastAPI interface
- a SQLite-first local memory store with a future upgrade path
- a model-agnostic action layer with adapter boundaries
- a bounded evolution system where all durable changes are reviewable and reversible

We will keep personal runtime state in `.local/` and keep the tracked repository clean enough to push to the private GitHub remote without exporting private memory by default.

## Consequences

Positive:

- simpler developer experience for a solo builder
- easier Codex navigation and delegation
- durable audit trail for prompts, policies, and architecture
- clear separation between private runtime state and tracked artifacts

Negative:

- some runtime state is intentionally outside Git history
- self-improvement remains slower because approvals and rollback paths are mandatory
- future migrations to richer storage or orchestration need explicit interface work

## Rejected Alternatives

- GitHub-centric runtime: rejected because local runtime must remain primary
- memory-in-repo by default: rejected because personal memory should stay private and local-first
- microservice split: rejected because it adds operational weight too early

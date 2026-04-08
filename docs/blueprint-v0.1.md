# Skylattice Blueprint v0.1

## Summary

Skylattice v0.1 establishes a serious local-first foundation for a personal evolvable agent. The tracked repository holds the architecture, governance, prompts, skills, and evaluation surface. Sensitive runtime state and personal memory stay in `.local/`.

## System Intent

The system exists to support a single user over time through:

- stable identity
- durable multi-layer memory
- bounded real-world action capability
- reversible self-improvement
- Git-native auditability

## Scope For v0.1

In scope:

- repository structure and navigation
- architecture and governance documents
- minimal Python package and FastAPI stub
- CLI health and kernel summary entry point
- explicit interfaces for memory, actions, planning, evolution, and ledger

Out of scope:

- autonomous background execution engine
- rich browser automation
- production-grade GitHub automation
- vector database coupling
- large-scale evaluation infrastructure

## Non-Negotiable Invariants

- Local runtime must work without GitHub.
- GitHub remains important for audit, sync, and optional issue or PR planning.
- Personal memory is private by default and must not silently leak into tracked artifacts.
- Self-improvement only changes reviewable artifacts or local state with rollback paths.
- Governance beats convenience: destructive, external, or self-modifying actions require explicit approval.

## Tracked Versus Local State

Tracked:

- docs and ADRs
- prompt files
- skills and playbooks
- evaluation scenarios and redacted reports
- interface definitions and runtime stubs

Local-only:

- live memory records
- user-specific overrides
- run logs
- sandbox outputs
- exported raw interaction evidence

## Main Subsystems

- `kernel`: stable identity, mission, relationship model, runtime snapshot
- `memory`: layered recall, abstraction, and compaction rules
- `actions`: model-agnostic tool and adapter boundary
- `planning`: goal interpretation, decomposition, execution tracking
- `governance`: approvals, budgets, freezes, destructive guards
- `evolution`: observe, reflect, propose, sandbox, evaluate, promote or rollback
- `ledger`: append-only audit events for decisions and state changes

## Main Risks

- mixing the private local runtime with the publishable repository surface
- letting prompts or policies drift without reviewable history
- overbuilding infrastructure before the memory and governance semantics are stable
- treating GitHub as operational truth instead of audit surface

## Open Questions Deferred Past v0.1

- which vector backend, if any, should power semantic recall
- whether background jobs should remain local cron-based or move to a richer scheduler
- how much GitHub issue or PR planning should be automated
- what evaluation gates are required before the evolution loop can promote changes automatically

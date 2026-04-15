# ADR 0005: Review-Driven Memory Operations And Retrieval Integration

- Status: Accepted
- Date: 2026-04-14

## Context

Skylattice already persisted profile, episodic, semantic, procedural, and working memory in local SQLite state, but memory was still mostly a write-only audit surface. The task agent did not retrieve memory during planning, and operators had no explicit local workflow for reviewing profile updates, semantic compaction, procedural deduplication, or memory export.

That left a gap between the documented blueprint and the runtime:

- memory existed, but it did not yet shape live task planning
- profile updates were described as reviewed, but there was no review flow
- semantic and procedural compaction rules were documented, but there was no explicit operator path to apply them

## Decision

We turn memory into a review-driven local subsystem while keeping Skylattice CLI-first and read-only over HTTP.

Key decisions:

- reuse `memory_records` instead of creating a separate proposal table
- activate `RecordStatus.CONSTRAINED` as the single pending-review state
- add CLI-first memory workflows for proposing, confirming, rejecting, searching, exporting, and rolling back records
- keep FastAPI read-only and add only record inspection and search endpoints
- integrate ranked profile, procedural, and semantic memory retrieval into task planning through a bounded `memory_context`
- keep retrieval deterministic and SQLite-only; no vector backend or embeddings in this milestone
- keep semantic compaction and procedural dedup explicit; no scheduler or background mutation

## Consequences

Positive:

- task planning can now use durable local memory without widening runtime autonomy
- profile edits and memory cleanup become explicit, reviewable operator actions
- memory exports remain local-only while becoming easier to inspect and back up
- procedural and semantic memory can mature without hidden heuristics

Tradeoffs:

- review flows add more operator steps than a fully automatic memory system
- retrieval remains transparent and conservative rather than semantically deep
- compaction quality is deterministic and bounded, not model-generated

## Rejected Alternatives

- separate memory proposal tables: rejected because existing record states already support review semantics
- background compaction jobs: rejected because they hide mutation timing and make rollback harder to reason about
- embeddings or vector search now: rejected because the project still benefits more from legible local ranking than from opaque retrieval infrastructure
- mutable API endpoints for memory review: rejected because CLI remains the primary local operator surface

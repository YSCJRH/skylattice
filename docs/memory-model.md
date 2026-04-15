# Memory Model

Skylattice keeps memory layered, local-first, and reviewable. Memory is no longer just a write-only audit trail: operators can now review local proposals, search ranked memory, export records under `.local/`, and feed bounded memory context into task planning.

## Record States

Memory records move through four explicit states:

- `active`: live memory eligible for normal retrieval
- `constrained`: pending operator review for profile updates, semantic compaction, or procedural dedup
- `superseded`: replaced by a newer confirmed record but preserved for provenance
- `tombstoned`: rolled back or rejected without deleting history

`constrained` is the only pending-review state. Skylattice does not use a separate proposal table.

## Retrieval Rules

Retrieval stays SQLite-first and deterministic.

- profile, procedural, and semantic memory can be searched by the current task goal
- exact case-insensitive summary matches rank highest
- token overlap in summaries ranks next
- token overlap in string metadata values provides a smaller boost
- active records outrank stale records when stale records are included
- recency provides a small tie-breaking bonus
- final ordering breaks ties by `created_at DESC`, then `record_id`

Task planning receives only a bounded `memory_context` with top-ranked profile, procedural, and semantic records. Retrieval does not grant extra permissions or validation scope.

## Profile Memory

- Purpose: stable user facts, preferences, and standing constraints
- Write path: `skylattice memory profile propose ...` creates a `constrained` record
- Confirmation: `skylattice memory review confirm <record_id>` activates the proposal and supersedes the active record with the same `profile_key`
- Rejection: `skylattice memory review reject <record_id>` tombstones the proposal
- Retrieval: always eligible when directly relevant to planning or governance
- Rollback: `skylattice memory rollback <record_id>` tombstones the active record and preserves provenance

Profile metadata contract:

- `profile_key`
- `value`
- `reason`

## Episodic Memory

- Purpose: important task runs, radar scans, experiment outcomes, promotion and rollback events
- Write triggers: task completion, notable failure, radar run completion, promotion, rollback
- Retrieval: by recency and goal relevance
- Conflict style: append-only
- Rollback: preserve raw event history; do not delete records

## Semantic Memory

- Purpose: durable abstractions, patterns, and learned technical signals
- Write triggers: repeated episodes, validated reflections, radar shortlist synthesis
- Retrieval: ranked by topic and current planning need
- Compaction: explicit only via `skylattice memory semantic compact --create-proposals`
- Confirmation: activates the constrained summary and supersedes the source semantic records
- Rollback: tombstones the active summary while preserving the source lineage

Semantic metadata contract:

- `origin`
- `topic_tags`
- optional `compacted_from`

Radar rule:

- radar-created semantic records include `origin=radar`, `repo_slug`, `topic_tags`, `confidence`, and `evidence_refs`

## Procedural Memory

- Purpose: playbooks, skills, reusable workflows, tool routing preferences, and adopted radar behavior
- Write triggers: successful repeated workflow, reviewed skill update, successful radar promotion
- Retrieval: when the current task matches an approved procedure or workflow
- Dedup: explicit only via `skylattice memory procedural dedup --create-proposals`
- Confirmation: activates a canonical workflow record and supersedes duplicate active records in the same `workflow`
- Rollback: tombstones the active canonical record without deleting prior records

Procedural metadata contract:

- `workflow`
- `canonical`

Task and radar writes use stable workflow names so review tooling can group related procedures later.

## Working Memory

- Purpose: task-local or radar-run-local scratch state
- Write triggers: plan creation, active execution step, temporary finding, active radar scan
- Retrieval: only within the active run
- Decay: clear on run close or summarize into episodic memory
- Rollback: clear by tombstoning the working record at run finalization

## Operator Surfaces

CLI is the write surface for memory review:

- `skylattice memory list`
- `skylattice memory inspect`
- `skylattice memory search`
- `skylattice memory profile propose`
- `skylattice memory review list|confirm|reject`
- `skylattice memory semantic compact --create-proposals`
- `skylattice memory procedural dedup --create-proposals`
- `skylattice memory rollback`
- `skylattice memory export`

FastAPI remains read-only:

- `GET /memory/records/{record_id}`
- `GET /memory/search`

## Storage Notes

- tracked schema and policy live in the repository
- private memory records and exports stay under `.local/`
- default export path is `.local/memory/exports/<timestamp>.json`
- radar does not export raw GitHub payloads into tracked docs by default; only curated experiments, promotion logs, and adoption registry entries become tracked artifacts

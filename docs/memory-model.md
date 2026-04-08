# Memory Model

Skylattice keeps memory layered, local-first, and reviewable. The technology radar now activates semantic and procedural memory more explicitly instead of leaving them as future-only abstractions.

## Profile Memory

- Purpose: stable user facts, preferences, and standing constraints
- Write triggers: explicit user statement, confirmed durable preference, reviewed operator decision
- Retrieval: always eligible when directly relevant to planning or governance
- Decay/compaction: rare; supersede only when invalidated
- Conflict resolution: `supersede`
- Edit/rollback: explicit confirmation only; keep prior version and tombstone replacements

## Episodic Memory

- Purpose: important task runs, radar scans, experiment outcomes, promotion and rollback events
- Write triggers: task completion, notable failure, radar run completion, promotion, rollback
- Retrieval: by recency, run id, and topic relevance
- Decay/compaction: summarize repeated episodes upward into semantic memory
- Conflict resolution: append-only
- Edit/rollback: preserve raw run history; roll back only derived summaries

## Semantic Memory

- Purpose: durable abstractions, patterns, and learned technology signals
- Write triggers: repeated episodes, validated reflections, radar shortlist synthesis
- Retrieval: topic, capability gap, and current planning need
- Decay/compaction: periodic summarization with provenance retained
- Conflict resolution: `supersede`
- Edit/rollback: version summaries and preserve prior abstraction ids

Radar rule:

- semantic entries created by the radar must include `origin=radar`, `repo_slug`, `topic_tags`, `confidence`, and `evidence_refs`

## Procedural Memory

- Purpose: playbooks, skills, reusable workflows, tool routing preferences, and adopted radar behavior
- Write triggers: successful repeated workflow, reviewed skill update, successful radar promotion
- Retrieval: when the current task or scan matches an approved procedure
- Decay/compaction: replace only after a better reviewed procedure exists
- Conflict resolution: `supersede`
- Edit/rollback: use Git history for tracked artifacts and local snapshots for runtime routing state

Radar rule:

- successful promotions refresh procedural memory to note which external pattern was adopted and where the tracked behavior change lives

## Working Memory

- Purpose: task-local or radar-run-local scratch state
- Write triggers: plan creation, active execution step, temporary finding, active radar scan
- Retrieval: only within the active run
- Decay/compaction: clear or summarize on run close
- Conflict resolution: append-only
- Edit/rollback: clear at close; export only selected context into episodic memory

## Storage Notes

- tracked schema and policy live in the repository
- private memory records and indexes stay under `.local/`
- radar does not export raw GitHub payloads into tracked docs by default; only curated experiments, promotion logs, and adoption registry entries become tracked artifacts

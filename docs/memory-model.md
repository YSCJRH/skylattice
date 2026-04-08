# Memory Model

## Principles

- durable memory beats giant prompts
- sensitive memory stays local-first
- every durable abstraction needs provenance
- edits must be reversible
- conflicts must be explicit, not silent

## Storage Posture

Skylattice uses a dual-layer memory posture:

- tracked layer: schemas, policy definitions, export formats, redacted examples
- local layer: real personal memory records, indexes, embeddings, and rollback snapshots

## Memory Layers

| Layer | Storage purpose | Write triggers | Retrieval policy | Decay / compaction | Conflict resolution | Edit / rollback |
| --- | --- | --- | --- | --- | --- | --- |
| Profile | stable user facts, preferences, and standing constraints | explicit user statements, repeated confirmed preferences, durable operator decisions | always eligible for recall; highest priority when directly relevant | rare compaction; only when superseded or invalidated | supersede old fact with provenance | keep prior version and tombstone old claim |
| Episodic | important interactions, task outcomes, and events | completed tasks, notable failures, commitments, important conversation turns | retrieve by recency, tags, and similarity to current plan | summarize into semantic memory when patterns stabilize | append new event; never overwrite raw episode | event log plus derived summary rollback |
| Semantic | abstracted durable patterns and lessons | repeated episodes, validated reflections, cross-task patterns | retrieve by topic, capability, and current goal | periodic compaction toward higher-signal summaries | supersede summary with evidence links | version summaries and keep prior abstraction |
| Procedural | skills, playbooks, reusable workflows, routing preferences | successful repeatable workflows, reviewed prompt or skill updates | retrieve when task type matches known procedure | prune stale procedures when replaced by better reviewed versions | replace only through reviewed promotion | Git history for tracked artifacts, local snapshots for runtime routing |
| Working | current task-local context and scratch state | active plan creation, current run steps, temporary findings | always scoped to active task only | discard or summarize at task close | overwrite within task scope is allowed | clear on task close; optional episodic export |

## Retrieval Policy By Default

1. start with profile and active working memory
2. add semantic and procedural memory relevant to the current goal
3. add episodic evidence only when it improves grounding or provenance
4. refuse recall when confidence is low and ask for confirmation instead of inventing continuity

## Write Discipline

- profile writes require confidence and explicit provenance
- episodic writes happen at task boundaries or significant events
- semantic writes require evidence from multiple episodes or reviews
- procedural writes require a reviewed reusable workflow
- working memory is the only layer allowed to be freely rewritten during execution

## Compaction Rules

- no silent deletion of durable memory
- compaction produces a new record plus a link to source material
- stale records are marked constrained, superseded, or tombstoned
- local rollback snapshots must exist before destructive compaction steps

## Export And Rollback

- local memory exports must be explicit and redacted before entering the tracked repository
- rollback operates at record or snapshot granularity
- tracked procedural or prompt changes roll back through Git
- local semantic or profile changes roll back through local snapshot references

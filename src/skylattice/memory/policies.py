"""Default memory policies for the Skylattice bootstrap."""

from __future__ import annotations

from dataclasses import dataclass

from .interfaces import ConflictStrategy, MemoryLayer


@dataclass(frozen=True)
class MemoryLayerPolicy:
    layer: MemoryLayer
    purpose: str
    write_triggers: tuple[str, ...]
    retrieval_policy: str
    decay_policy: str
    conflict_resolution: ConflictStrategy
    rollback_mechanism: str


def default_memory_policies() -> dict[MemoryLayer, MemoryLayerPolicy]:
    return {
        MemoryLayer.PROFILE: MemoryLayerPolicy(
            layer=MemoryLayer.PROFILE,
            purpose="Stable user facts, preferences, and standing constraints.",
            write_triggers=(
                "Explicit user statement",
                "Repeated confirmed preference",
                "Durable operator decision",
            ),
            retrieval_policy="Always eligible when directly relevant to the current goal.",
            decay_policy="Rare compaction; supersede only when invalidated or replaced.",
            conflict_resolution=ConflictStrategy.SUPERSEDE,
            rollback_mechanism="Keep the prior fact version and tombstone the replaced claim.",
        ),
        MemoryLayer.EPISODIC: MemoryLayerPolicy(
            layer=MemoryLayer.EPISODIC,
            purpose="Important interactions, task outcomes, and event traces.",
            write_triggers=(
                "Completed task",
                "Notable failure or correction",
                "Important commitment",
            ),
            retrieval_policy="Retrieve by recency, tags, and relevance to the active plan.",
            decay_policy="Summarize upward into semantic memory after repeated patterns emerge.",
            conflict_resolution=ConflictStrategy.APPEND_ONLY,
            rollback_mechanism="Preserve the raw event log and roll back only derived summaries.",
        ),
        MemoryLayer.SEMANTIC: MemoryLayerPolicy(
            layer=MemoryLayer.SEMANTIC,
            purpose="Durable abstractions, lessons, and recurring user patterns.",
            write_triggers=(
                "Repeated episodes",
                "Validated reflection",
                "Cross-task pattern",
            ),
            retrieval_policy="Retrieve by topic, capability, and current planning need.",
            decay_policy="Compact periodically into higher-signal summaries with provenance.",
            conflict_resolution=ConflictStrategy.SUPERSEDE,
            rollback_mechanism="Version summaries and retain references to prior abstractions.",
        ),
        MemoryLayer.PROCEDURAL: MemoryLayerPolicy(
            layer=MemoryLayer.PROCEDURAL,
            purpose="Skills, playbooks, reusable workflows, and routing preferences.",
            write_triggers=(
                "Successful repeated workflow",
                "Reviewed skill update",
                "Validated routing preference",
            ),
            retrieval_policy="Retrieve when a task matches an approved procedure or skill.",
            decay_policy="Prune or replace only after a better reviewed procedure exists.",
            conflict_resolution=ConflictStrategy.SUPERSEDE,
            rollback_mechanism="Use Git history for tracked artifacts and snapshots for local runtime routing.",
        ),
        MemoryLayer.WORKING: MemoryLayerPolicy(
            layer=MemoryLayer.WORKING,
            purpose="Current task-local context and scratch state.",
            write_triggers=(
                "Plan creation",
                "Current execution step",
                "Temporary finding",
            ),
            retrieval_policy="Always scoped to the active task only.",
            decay_policy="Clear or summarize on task close.",
            conflict_resolution=ConflictStrategy.APPEND_ONLY,
            rollback_mechanism="Clear the working set at task close or export selected context to episodic memory.",
        ),
    }

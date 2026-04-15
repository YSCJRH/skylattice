# ADR 0010: Explicit Destructive Repo Approval

- Status: Accepted
- Date: 2026-04-15

## Context

Skylattice already supported deterministic text edits plus non-destructive tracked file primitives, but one important gap remained:

- delete and move workflows still had to stay outside the task-agent path because governance denied destructive actions outright
- `repo-write` approval alone was too coarse to double as blanket permission for destructive tracked file lifecycle changes
- the runtime needed a way to support reviewable cleanup and file moves without weakening the default destructive guard

That left task-agent expressive enough for scaffolding work, but still awkward for bounded refactors that require removing or relocating tracked files.

## Decision

We add explicit destructive repo primitives and require a second operator approval for them.

Key decisions:

- support `move_file` and `delete_file` as first-class task operation modes for tracked-safe text files
- keep their execution deterministic and local: no directory lifecycle ops, no shell-based delete/move fallback
- require both `repo-write` and `destructive-repo-write` before destructive tracked repo steps can execute
- record destructive status and recommended allow flags in recovery metadata so blocked runs remain auditable and resumable

## Consequences

Positive:

- task-agent can now express bounded cleanup and tracked file relocation work without dropping to ad hoc manual steps
- destructive approval becomes explicit and reviewable instead of being hidden inside generic repo-write consent
- recovery surfaces can distinguish ordinary repo edits from higher-risk destructive steps

Tradeoffs:

- operators now have one more approval flag to understand for destructive task runs
- planner and runtime contracts gain two more file operation modes
- destructive file handling remains intentionally narrow and does not solve broader tree-shaping workflows

## Rejected Alternatives

- keep rejecting all destructive repo work: rejected because bounded cleanup and rename work are legitimate repo tasks that should be auditable inside the same runtime
- treat destructive ops as ordinary `repo-write`: rejected because it weakens the current governance boundary and blurs the difference between editing and deleting
- add broad directory or shell-based destructive automation: rejected because it expands side-effect scope faster than the current recovery and governance model is ready for

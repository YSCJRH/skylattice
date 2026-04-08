# ADR 0002: CLI-First Task Agent MVP

- Status: Accepted
- Date: 2026-04-08

## Context

Skylattice had a solid architectural foundation but no real execution loop. The next step needed to make the system truly usable for the solo-builder workflow without jumping straight to a broad autonomous platform.

## Decision

We will implement the next milestone as a CLI-first task-agent MVP with one narrow end-to-end lane:

- accept a repo task from the CLI
- generate a constrained plan through the OpenAI Responses API
- enforce governance step by step
- execute local repo edits and Git actions
- push only after explicit approval
- sync a draft PR or issue comment through direct GitHub API calls
- persist runs, approvals, events, and memory in local SQLite state

The main write interface is the CLI. FastAPI remains read-only for run inspection.

## Consequences

Positive:

- the project becomes genuinely executable instead of remaining a design shell
- the runtime stays local-first and inspectable
- approvals and resume behavior are explicit and replayable
- GitHub becomes a real audit surface without being a runtime dependency

Negative:

- the first execution lane is intentionally narrow
- the planner and file rewrite flow depend on external model calls when using the real provider
- richer code edits, browser automation, and recovery logic remain future work

## Rejected Alternatives

- API-first task runtime: rejected because the builder workflow is primarily local and CLI-driven
- `gh` CLI as the only GitHub transport: rejected because the runtime should be able to operate through a direct API abstraction
- broad general agent scope: rejected because a narrow vertical slice is safer and easier to govern

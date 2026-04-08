# Comparison

Skylattice is intentionally narrow. The point is not to out-feature every agent tool, but to make a specific design space legible: local-first memory, governed repo tasks, and bounded self-improvement.

## Category Comparison

| Category | What it usually optimizes for | What Skylattice optimizes for | Practical difference |
| --- | --- | --- | --- |
| Chat wrappers | fast conversation UX | durable runtime state plus operator-visible system boundaries | Skylattice is slower to explain, but easier to audit |
| Broad agent frameworks | flexible orchestration and tool breadth | a small, inspectable runtime with explicit approval tiers | Skylattice gives up breadth for clearer operational boundaries |
| Repo automation bots | pull requests, CI hooks, issue workflows | reviewable repo edits with materialized payloads, local memory, and ledger traces | Skylattice behaves more like a governed runtime than a workflow bot |
| Local knowledge tools | storage and retrieval | storage, action, governance, and Git-backed change review | Skylattice is about acting and evolving, not only remembering |

## Where Skylattice Is Stronger

- explicit approval boundaries for repo and external writes
- tracked validation policy shared by runtime and CI
- local-first memory posture with private state outside tracked Git history
- bounded radar promotion path with rollback metadata
- small enough codebase to inspect end to end

## Where Skylattice Is Intentionally Weaker

- fewer integrations than general-purpose agent frameworks
- no hosted control plane
- no AST refactor engine
- no arbitrary shell execution path in the task agent
- no promise of autonomous operation without review

## How To Position It Publicly

A good short description for Skylattice is:

> Local-first AI agent runtime for persistent memory, governed repo tasks, and Git-native self-improvement.

The most relevant topic families are:

- `local-first`
- `ai-agent`
- `agent-framework`
- `memory`
- `sqlite`
- `cli`
- `fastapi`
- `developer-tools`
- `github`
- `personal-agent`

## What Skylattice Is Not

- not a hosted assistant product
- not a drop-in replacement for every agent framework
- not a promise of autonomous code generation without operator review
- not a private memory export format meant for public commits

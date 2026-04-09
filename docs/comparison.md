---
title: Comparison
description: How Skylattice differs from broad agent frameworks, chat wrappers, repo automation bots, and local knowledge tools.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/comparison/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/comparison/
---

# Comparison

Skylattice is intentionally narrow. The point is not to out-feature every agent tool, but to make a specific design space legible: local-first memory, governed repo tasks, and bounded self-improvement.

## Key Takeaways

- Skylattice gives up breadth in exchange for clearer operator boundaries.
- It behaves more like a governed runtime than a workflow bot or prompt wrapper.
- It is strongest when you care about rollbackability, auditability, and tracked system behavior.

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

## One-Line Positioning

> Local-first AI agent runtime for persistent memory, governed repo tasks, and Git-native self-improvement.

## What Skylattice Is Not

- not a hosted assistant product
- not a drop-in replacement for every agent framework
- not a promise of autonomous code generation without operator review
- not a private memory export format meant for public commits

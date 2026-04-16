---
title: Comparison
description: Why Skylattice is not a generic agent framework, chat wrapper, or hosted bot, and where it is a better fit instead.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/comparison/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/comparison/
---

# Comparison

If you are searching for a local-first AI agent runtime or an auditable agent framework, the main difference is simple: Skylattice optimizes for reviewability and governance boundaries before it optimizes for breadth.

## Key Takeaways

- Skylattice gives up integration breadth in exchange for clearer operator boundaries.
- It behaves more like a governed runtime than a workflow bot, prompt wrapper, or hosted assistant.
- It is strongest when rollbackability, auditability, and Git-backed review matter more than tool count.

## Fast Category Check

Skylattice is probably the right category if you care most about:

- local-first state and memory boundaries
- understanding exactly what changed after a run
- keeping validation, approvals, and rollback visible in tracked artifacts

Skylattice is probably the wrong category if you care most about:

- broad tool ecosystems first
- fast hosted convenience
- autonomous execution breadth before review boundaries

## Why It Is Not A Generic Agent Framework

Generic agent frameworks usually optimize for flexible orchestration, many tools, and rapid experimentation. Skylattice starts from a different constraint: meaningful behavior should remain legible after the run, and meaningful writes should stay inside explicit governance boundaries.

That means Skylattice intentionally favors deterministic text edits, tracked validation, local-first state, and Git-native review surfaces over integration breadth.

## Category Comparison

| Category | What it usually optimizes for | What Skylattice optimizes for | Practical difference |
| --- | --- | --- | --- |
| Chat wrappers | fast conversation UX | durable runtime state plus operator-visible system boundaries | Skylattice is slower to explain, but easier to audit |
| Broad agent frameworks | flexible orchestration and tool breadth | a small, inspectable runtime with explicit approval tiers | Skylattice gives up breadth for clearer operational boundaries |
| Repo automation bots | pull requests, CI hooks, issue workflows | reviewable repo edits with materialized payloads, local memory, and ledger traces | Skylattice behaves more like a governed runtime than a workflow bot |
| Hosted assistants | convenience and cloud defaults | local-first memory posture and operator-owned state | Skylattice is for people who want the system legible on disk |
| Local knowledge tools | storage and retrieval | storage, action, governance, and Git-backed change review | Skylattice is about acting and evolving, not only remembering |

## Choose Skylattice When

- you want persistent memory plus governed repo tasks in the same system
- you need approval boundaries, tracked validation, and rollbackable Git changes
- you care about understanding what happened after a run, not only whether it succeeded
- you want to verify the system in layers instead of trusting live adapters immediately

## Choose Something Else When

- you need a hosted product or zero-config onboarding
- you want the widest possible integration surface first
- you need AST-aware refactors or unrestricted tool execution now
- you mainly want a coding copilot rather than an inspectable runtime with memory and governance

## What You Notice On First Contact

- broad agent frameworks usually show you tool breadth first
- chat wrappers usually show you interaction UX first
- Skylattice shows you proof surfaces, tracked validation, and governance boundaries first

That first impression is intentional. The project is optimized to help a cautious operator decide whether to trust it at all before asking for meaningful writes.

## One-Line Positioning

> Local-first AI agent runtime for persistent memory, governed repo tasks, and Git-native self-improvement.

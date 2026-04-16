---
title: Use Cases
description: The best-fit scenarios for Skylattice, including local-first personal agents, governed repo tasks, and bounded open-source learning loops.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/use-cases/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/use-cases/
---

# Use Cases

Skylattice is most useful for people who care about agent systems as infrastructure, not just as prompts.

If you want a local-first runtime that is legible to operators, reviewable in Git, and explicit about governance boundaries, these are the current best-fit scenarios.

## Key Takeaways

- Skylattice is a strong fit when you want memory, action, and review boundaries in the same system.
- It is better as a governance-heavy reference runtime than as a broad automation platform.
- It is especially useful when you want to inspect what happened after a run, not only whether it passed.

## Fast Decision Check

Choose Skylattice first when your main question sounds like one of these:

- "How do I keep a personal agent's state local without hiding its behavior?"
- "How do I let an agent touch a repo without giving it unbounded shell freedom?"
- "How do I learn from open source and still keep every behavior change reviewable in Git?"

Choose something else first when your main question sounds like one of these:

- "How do I get a hosted assistant working today with minimal setup?"
- "How do I maximize integrations, tool count, or autonomous execution breadth?"
- "How do I run broad code refactors or arbitrary shell workflows right now?"

## 1. Keep A Personal Agent Local, Durable, And Reviewable

Choose Skylattice when you want a personal agent runtime that:

- keeps real runtime memory under `.local/` instead of tracked Git history
- stores durable system behavior in legible docs, prompts, configs, and ADRs
- exposes health, run, memory, and radar inspection surfaces you can read without mutating state

Why it matters:

- you can grow a long-lived agent without turning the repo into a pile of opaque hidden state
- you can inspect what the system believes about itself before giving it more autonomy
- you can decide whether the boundary design is good enough for you before trusting live adapters

## 2. Run Governed Repo Tasks Instead Of Unbounded Automation

Choose Skylattice when you want repo work that stays bounded:

- the planner declares file operations and validation commands up front
- repo and external writes still pass through approval gates
- task edits are deterministic and text-native, not arbitrary shell automation
- run inspection shows ledger events, materialized edit payloads, and memory writes after execution

Why it matters:

- you can understand what happened after a run, not just whether it passed
- you can use the project as a reference for reviewable AI-assisted repo operations
- you can separate "credential wiring works" from "I want this system to write to my repo"

## 3. Learn From Open Source Without Turning The Runtime Into A Black Box

Choose Skylattice when you want a radar workflow that:

- discovers GitHub projects through tracked topics and scoring rules
- records evidence, experiments, promotions, and rollback metadata in a local ledger
- limits automatic promotion to whitelisted tracked paths
- keeps adoption state in `configs/radar/adoptions.yaml` instead of hidden model behavior

Why it matters:

- you can experiment with bounded self-improvement without giving the runtime silent write access everywhere
- you can inspect what the system learned, why it promoted something, and how to roll it back
- you can keep provider rollout, schedule intent, and promotion policy visible as tracked artifacts

## Who Should Care Today

- builders exploring local-first agent infrastructure
- contributors who want a small, inspectable reference repo for governance-heavy automation
- people comparing durable memory patterns, repo-task execution models, and Git-native rollback strategies

## Who Should Wait

Skylattice is still early if you need:

- a polished hosted product
- zero-config autonomous execution
- AST-aware refactors or arbitrary shell workflows
- a framework that optimizes for breadth over explicit operational boundaries

## Best Current Fit

The strongest current fit is a builder who wants a compact, inspectable system they can verify in stages:

1. prove the zero-credential local baseline
2. verify live credentials with read-only smoke checks
3. decide whether governed task runs or the radar workflow are worth deeper adoption

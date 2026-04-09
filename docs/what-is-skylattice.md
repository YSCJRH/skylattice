---
title: What Is Skylattice?
description: Skylattice is a local-first AI agent runtime that combines durable memory, governed repo tasks, and Git-native self-improvement.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/what-is-skylattice/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/what-is-skylattice/
---

# What Is Skylattice?

Skylattice is a local-first AI agent runtime for people who want an agent they can inspect like software.

Instead of hiding state in prompts or cloud services, Skylattice keeps private runtime memory under `.local/`, keeps durable system behavior in tracked files, and routes meaningful changes through reviewable Git history.

## Key Takeaways

- It is optimized for auditability, reversibility, and explicit governance instead of broad automation breadth.
- It already demonstrates governed repo tasks and a bounded technology-radar workflow.
- It is a good fit if you care about durable memory, clear approval boundaries, and Git-backed review surfaces.

## What It Already Does

- stores runtime state in local SQLite-backed storage
- exposes `doctor`, `task ...`, and `radar ...` CLI paths
- records run inspection data, ledger events, and materialized edit payloads
- uses tracked validation commands that align CI and runtime policy

## Read Next

- [Quick start](quickstart.md)
- [Use cases](use-cases.md)
- [Comparison](comparison.md)
- [Proof](proof.md)

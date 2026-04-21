---
title: Category / Comparison Post Draft
description: Execution-grade comparison article for explaining where Skylattice fits relative to broad agent frameworks, chat wrappers, and hosted automation products.
robots: noindex, follow
---

# Category / Comparison Post Draft

## Recommended Title

Why Skylattice is not a generic agent framework

## Publishable Draft

Skylattice does not compete on the same axis as most agent frameworks. If you want the widest possible tool surface, the fastest orchestration experiments, or a hosted assistant experience, there are better fits.

Skylattice is for a narrower design space: local-first memory, governed repo tasks, and Git-native reviewability. That combination matters when you want the runtime legible after the run, not only impressive during the demo.

A broad framework usually asks, ?what can this agent call?? Skylattice also asks, ?where does its private state live, what changed after the run, which approvals were required, and how would you roll it back??

That is why the repository looks unusual. Docs, configs, prompts, ADRs, validation policy, release notes, and proof artifacts are all part of the product surface. The goal is not to hide the system behind magic. The goal is to make the system inspectable enough that a serious builder can decide whether to trust it.

## What Skylattice Optimizes For

- durable local memory instead of opaque cloud defaults
- governed repo tasks instead of unbounded automation
- tracked validation policy shared by runtime and CI
- Git-native change review, release notes, and rollback surfaces

## What Skylattice Intentionally Does Not Optimize For

- the broadest integration surface
- hosted control-plane convenience
- AST-aware refactor breadth
- hands-off autonomous code generation without review

## Best Link Targets

- comparison page: `https://yscjrh.github.io/skylattice/comparison/`
- what-is page: `https://yscjrh.github.io/skylattice/what-is-skylattice/`
- proof page: `https://yscjrh.github.io/skylattice/proof/`
- stable release: `https://yscjrh.github.io/skylattice/releases/v0-3-1/`

## Suggested CTA

If you want to understand the project quickly, read the comparison page first, then the proof page, then the stable release page.

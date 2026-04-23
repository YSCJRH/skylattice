---
title: What Is Skylattice?
description: Skylattice is a local-first AI agent runtime and auditable agent framework for durable memory, governed repo tasks, and Git-native reviewability.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/what-is-skylattice/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/what-is-skylattice/
jsonld: |
  {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    "name": "Skylattice",
    "description": "Local-first AI agent runtime and auditable agent framework for durable memory, governed repo tasks, and Git-native reviewability.",
    "codeRepository": "https://github.com/YSCJRH/skylattice",
    "softwareVersion": "0.4.1",
    "license": "https://github.com/YSCJRH/skylattice/blob/main/LICENSE",
    "inLanguage": "en"
  }
---

# What Is Skylattice?

Skylattice is a local-first AI agent runtime for people who want a persistent-memory agent they can inspect like software.

It combines private local memory, governed repo tasks, and Git-native review surfaces so the system stays auditable instead of drifting behind hidden prompts or opaque cloud state.

## Key Takeaways

- Skylattice is an auditable agent framework, not a chat wrapper or a broad coding-bot platform.
- It is strongest when you care about governed repo tasks, rollbackable changes, and durable local memory.
- You can verify the runtime without API keys, then inspect stable release notes, scheduler surfaces, and public-safe sample outputs.

## What Makes It Different

- local runtime state lives under `.local/` instead of inside tracked Git history
- durable behavior lives in docs, configs, prompts, ADRs, and tests that operators can review
- repo and external writes stay behind approval gates and tracked validation commands
- bounded self-improvement runs through Git-backed radar promotions rather than silent prompt drift

## Good Fit Today

- builders exploring local-first AI agent infrastructure
- contributors who want governed repo-task automation with ledger traces and inspectable edit payloads
- teams comparing durable memory patterns, approval boundaries, and Git-native rollback strategies

## Not The Best Fit Yet

- users expecting a hosted assistant product
- teams needing broad integrations before they care about auditability
- workflows that require AST-aware refactors or unrestricted shell automation

## Read Next

- [Quick start](quickstart.md)
- [Use cases](use-cases.md)
- [Comparison](comparison.md)
- [Proof](proof.md)
- [v0.4.1 Stable](releases/v0-4-1.md)

---
title: FAQ
description: Frequently asked questions about what Skylattice is, who it is for, how to verify it, and how it differs from broader agent frameworks.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/faq/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/faq/
jsonld: |
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "What is Skylattice used for?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Skylattice is used as a local-first AI agent runtime and as a reference implementation for durable memory, governed repo tasks, and Git-native self-improvement."
        }
      },
      {
        "@type": "Question",
        "name": "Is Skylattice a generic coding agent framework?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "No. Skylattice is intentionally narrower than broad agent frameworks. It emphasizes inspectability, governance boundaries, tracked validation, and rollbackable Git changes."
        }
      },
      {
        "@type": "Question",
        "name": "Can I verify Skylattice without API keys?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Yes. You can install the project, run skylattice doctor, run pytest, run the tracked validation suite, and inspect redacted sample outputs without adding credentials."
        }
      }
    ]
  }
---

# FAQ

Skylattice is easiest to understand through concrete questions.

## What is Skylattice used for?

Skylattice is used for two things today: running a local-first agent runtime with explicit governance boundaries, and studying a compact reference design for durable memory plus governed repo automation.

## Is Skylattice a generic coding agent framework?

No. Skylattice is intentionally narrower than broad agent frameworks. It trades breadth for explicit approval tiers, tracked validation policy, and Git-backed reviewability.

## Can I verify Skylattice without API keys?

Yes. Follow the [quick start](quickstart.md), run `doctor`, run the tests, and inspect the redacted outputs under `examples/redacted/`.

## Does Skylattice store memory in Git?

No. Private runtime memory stays under `.local/`. Tracked Git history stores docs, prompts, configs, ledgers, and other reviewable system behavior.

## Is Skylattice a hosted product?

No. It is an early public preview of a local-first runtime and reference repo, not a hosted assistant or managed platform.

## Where should I look for proof?

Start with [proof.md](proof.md), the [release page](releases/v0-2-0.md), and the sample outputs linked from the [quick start](quickstart.md).

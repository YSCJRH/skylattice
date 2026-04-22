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
          "text": "Skylattice is used as a local-first AI agent runtime and as a compact reference implementation for durable memory, governed repo tasks, and Git-native self-improvement."
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
        "name": "How do I verify Skylattice without API keys?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Install the project, run skylattice doctor, run pytest, run the tracked validation suite, and compare your results with the public-safe sample outputs."
        }
      },
      {
        "@type": "Question",
        "name": "Why does Skylattice still say GitHub is not configured after gh auth login?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Because Skylattice does not automatically consume the GitHub CLI login state. Run skylattice doctor auth to see the missing runtime requirements, then use skylattice doctor github-bridge --format env if you intentionally want explicit environment exports."
        }
      },
      {
        "@type": "Question",
        "name": "Does Skylattice store memory in Git?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "No. Private runtime memory stays under .local. Git history stores tracked docs, configs, prompts, ADRs, and other reviewable system behavior."
        }
      },
      {
        "@type": "Question",
        "name": "What does Git-native governance mean here?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "It means meaningful edits, validation policy, release notes, and bounded promotion paths are visible in tracked files and reviewable Git history instead of being hidden inside cloud defaults."
        }
      }
    ]
  }
---

# FAQ

Skylattice is easiest to understand through direct questions.

## What is Skylattice used for?

Skylattice is used for two things today: running a local-first agent runtime with explicit governance boundaries, and studying a compact reference design for durable memory plus governed repo automation.

## Is Skylattice a generic coding agent framework?

No. Skylattice is intentionally narrower than broad agent frameworks. It trades breadth for explicit approval tiers, tracked validation policy, Git-backed reviewability, and rollbackable change paths.

## How do I verify Skylattice without API keys?

Follow the [quick start](quickstart.md), run `doctor`, run the smoke tests, run the validation suite, and compare your outputs with the public-safe samples under `examples/redacted/`.

## What does the no-credential path actually prove?

It proves the local runtime boots, the tracked validation baseline is real, and the repository ships inspectable proof artifacts. It does not prove that the live OpenAI or GitHub adapters are configured for your machine yet.

## How do I check live credentials without jumping straight to repo writes?

Use the optional read-only authenticated smoke:

```bash
python tools/run_authenticated_smoke.py --provider github
python tools/run_authenticated_smoke.py --provider gitlab
python tools/run_authenticated_smoke.py --provider openai
```

This verifies live adapter connectivity without turning on repo-write or external-write task behavior.

## Why does Skylattice still say GitHub is not configured after `gh auth login`?

Because Skylattice does not automatically consume the GitHub CLI login state.

Use:

```bash
python -m skylattice.cli doctor auth
```

If you intentionally want explicit environment exports for the current shell, use:

```bash
python -m skylattice.cli doctor github-bridge --format env
```

This keeps the bridge explicit instead of silently widening runtime auth behavior.

## Does Skylattice store memory in Git?

No. Private runtime memory stays under `.local/`. Tracked Git history stores docs, configs, prompts, release notes, and other reviewable system behavior.

## What does Git-native governance mean here?

It means meaningful edits, validation rules, and promotion paths stay visible in tracked files and Git history. The project is designed so operators can review what changed and why.

## Is Skylattice a hosted product?

No. It is a local-first runtime and reference repository, not a managed assistant service.

## Where should I look for proof first?

Start with [proof.md](proof.md), the [quick start](quickstart.md), and the [v0.4.0 Stable release page](releases/v0-4-0.md).

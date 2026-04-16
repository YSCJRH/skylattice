# 2026-04-16 Onboarding Operator Pass

## Scope

- date: 2026-04-16
- basis: structured repo review, handover analysis, live GitHub review, and the merged follow-up work from PRs `#22`, `#23`, and `#24`
- artifact type: internal operator synthesis
- not included: direct cold-visitor interviews, survey data, or public community responses

## What This Pass Is

This record is an operator pass after a full repository handover, not a claim that Skylattice has already collected meaningful external user feedback.

It exists to capture what became clear during the handover and the immediate follow-up work, so issues `#2`, `#3`, and `#4` can reference one tracked summary instead of relying on chat history.

## Main Friction Points Observed

### 1. The no-credential path proved reality, but not its boundary, quickly enough

Before the latest docs pass, the quick start told a visitor what to run, but not fast enough what that sequence did and did not prove.

The clearest missing distinction was:

- zero-credential verification proves the local runtime, tracked validation baseline, and proof artifacts
- it does not prove live OpenAI or GitHub adapter wiring

### 2. There was no repo-native bridge from zero-credential proof to live credential validation

Before the authenticated smoke work, the repo had a gap between:

- "the local baseline is real"
- "I am ready to let this touch real providers"

That gap made token-enabled adoption feel riskier than it needed to, because the first live step implied much more than a simple connectivity check.

### 3. Visitors still needed a faster category-fit decision

The repo already had good comparison and use-case pages, but the decision still took too many paragraphs:

- is Skylattice a framework, a bot, a hosted assistant, or a governed runtime?
- should I keep reading if I mostly want convenience and breadth?
- should I keep reading if I care about auditability and rollback first?

### 4. The project was easier to trust than to classify

By the time a careful operator finished the review, the repo looked disciplined and credible. But that confidence came later than the initial category decision.

In other words:

- trust signal: strong
- category-fit signal on first contact: improving, but still slower than ideal

## Changes Landed During This Pass

### Already merged in `main`

- PR `#22`: handover baseline, Phase 5 decision frame, first weekly radar validation record, prompt truth-source alignment, and `.local/work` path-protection fix
- PR `#23`: opt-in authenticated smoke validation for live GitHub and OpenAI adapter checks
- PR `#24`: onboarding and positioning clarity pass across `quickstart`, `use-cases`, `comparison`, and `faq`

### Practical effect of those merges

- the docs now say more clearly what the five-minute path proves and what it does not
- the repo now supports a staged adoption path:
  1. zero-credential proof
  2. read-only authenticated smoke
  3. token-enabled task or radar workflows
- the category comparison now helps a visitor reject the repo faster when it is the wrong fit

## Remaining Unknowns

- whether cold visitors now understand the no-credential path faster without extra guidance
- whether the read-only authenticated smoke is actually discoverable enough in practice
- whether the revised comparison and use-case pages shorten time-to-fit-decision for non-expert readers
- whether the Chinese mirror surfaces need the same clarity upgrades after real user review

## Recommended Next Actions

- collect at least three cold-visitor impressions after the latest docs changes, and tag each finding as:
  - no-credential friction
  - category-fit confusion
  - trust / recommendation hesitation
- use those findings to decide whether issues `#2`, `#3`, and `#4` can be closed, narrowed, or split
- if confusion remains high, add one compact decision graphic or flowchart instead of only adding more prose

## Issue Mapping

- issue `#2`: partially addressed by clarifying proof boundaries and adding the authenticated smoke bridge; still needs actual first-run feedback
- issue `#3`: partially addressed by the comparison and use-case clarity pass; still needs real external wording feedback
- issue `#4`: still open by design, because this artifact is an internal operator synthesis rather than external onboarding feedback

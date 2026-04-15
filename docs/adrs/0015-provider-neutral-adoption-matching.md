# ADR 0015: Provider-Neutral Adoption Matching

## Status

Accepted

## Context

Phase 5 already introduced:

- tracked radar provider selection
- provider-neutral candidate and evidence identity fields

However, the adoption registry and scoring boost still matched primarily on `repo_slug`.

That works while GitHub is the only live provider, but it leaves a hidden GitHub-shaped rule in a place that will matter immediately when a second provider is evaluated:

- promotion would write richer identity, but scoring would still only trust `repo_slug`
- future providers would need to synthesize repository-like slugs to receive direct adoption credit
- the tracked adoption registry would not be the true source of identity matching semantics

## Decision

Adoption records now support provider-neutral identity fields:

- `source_provider`
- `source_kind`
- `source_handle`
- `source_url`

Scoring boost now prefers matching on provider-neutral identity:

1. exact `source_provider + source_handle`
2. legacy `repo_slug` fallback
3. topic overlap fallback

Promotion writes the richer identity fields into the tracked adoption registry while keeping legacy fields for compatibility.

## Consequences

### Positive

- adoption matching now follows the same identity contract as radar candidates and evidence
- future providers can receive direct adoption credit without pretending to be GitHub repositories
- the tracked registry becomes the durable truth for identity-based boost semantics

### Negative

- adoption records now carry some temporary duplication during the compatibility period
- scoring logic becomes slightly more explicit and verbose

## Non-Goals

- this ADR does not introduce a second live provider
- it does not remove `repo_slug` from the adoption registry yet
- it does not widen promotion or scheduling semantics

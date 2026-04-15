# ADR 0016: Normalized Radar Evidence Taxonomy

## Status

Accepted

## Context

Phase 5 already introduced provider-neutral identity for radar candidates and evidence objects, but evidence kind labels still leaned on GitHub-shaped wording:

- `search-result`
- `repository`
- `release`

Those labels are understandable for GitHub, but they are not a durable cross-provider taxonomy.

## Decision

Radar evidence kinds now use a normalized provider-neutral vocabulary:

- `discovery-hit`
- `object-metadata`
- `release-metadata`

GitHub remains the only live source in this slice, but it now emits the normalized kinds directly.

Older stored evidence kinds remain readable through compatibility normalization on load.

## Consequences

### Positive

- future providers can map into a stable evidence vocabulary without reusing GitHub-only terms
- inspect payloads become easier to compare across providers
- no destructive migration is required for previously stored evidence rows

### Negative

- compatibility normalization remains necessary until older local state naturally rolls forward

## Non-Goals

- no second live provider
- no change to evidence payload structure beyond normalized kind values
- no change to promotion or scoring semantics in this ADR

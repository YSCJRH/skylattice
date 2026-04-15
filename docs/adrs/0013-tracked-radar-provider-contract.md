# ADR 0013: Tracked Radar Provider Contract

## Status

Accepted

## Context

Phase 5 already introduced a stable `RadarDiscoverySource` protocol, but the runtime still defaulted to GitHub whenever a GitHub adapter happened to be available.

That was acceptable while GitHub was the only live source, but it would become a poor boundary for the next slice:

- provider choice would remain implicit instead of reviewable
- operator-facing state would not show which provider contract was intended
- a future second provider could appear to be "wired in" by runtime conditions rather than tracked repo policy

Skylattice needs a structure where provider intent is explicit before a second live source exists.

## Decision

Radar provider selection is now driven by tracked config in `configs/radar/providers.yaml`.

This contract:

- declares the default provider id
- lists known provider entries, including disabled future slots
- keeps GitHub as the only enabled live provider in this slice
- allows `RadarService.from_repo()` to resolve a live source from tracked policy instead of hardcoded adapter presence

Operator-facing state now exposes:

- `default_provider`
- `enabled_providers`
- `source_provider`

This keeps provider provenance visible even when only one live provider is active.

## Consequences

### Positive

- future provider rollout can start with tracked contract changes before any second live source ships
- doctor and radar state snapshots make provider intent inspectable
- the runtime no longer silently treats GitHub availability as equivalent to provider policy

### Negative

- radar config now spans another tracked file that must stay aligned with docs and tests
- a misconfigured default provider can intentionally leave radar without a live source until the operator fixes the tracked config

## Non-Goals

- this ADR does not introduce a second live provider
- it does not widen radar promotion, experiment, or approval semantics
- it does not add hosted aggregation, browser scraping, or hidden source fusion

# ADR 0014: Provider-Neutral Radar Identity Contract

## Status

Accepted

## Context

Phase 5 already introduced:

- a stable `RadarDiscoverySource` interface
- tracked provider selection in `configs/radar/providers.yaml`

However, radar candidates and evidence still exposed mostly GitHub-shaped identity fields:

- `repo_slug`
- `repo_name`
- `html_url`

Those fields are still useful while GitHub remains the only live source, but they are not sufficient as the durable contract for future providers.

If Skylattice waits until a second live source exists, the first integration will have to either:

- fake GitHub-shaped values, or
- force a broader contract refactor under schedule and provider rollout pressure

## Decision

Skylattice now carries an explicit provider-neutral identity contract alongside the existing GitHub-oriented fields.

Radar candidates expose:

- `source_provider`
- `source_kind`
- `source_handle`
- `source_url`
- `display_name`

Radar evidence exposes:

- `provider_object_type`
- `provider_object_id`
- `provider_url`

The existing GitHub-specific fields remain for compatibility in this slice.

Inspect surfaces and operator-facing text now prefer the normalized identity where it helps keep provider provenance explicit.

## Consequences

### Positive

- future providers can plug into a stable identity contract before GitHub-shaped fields are retired
- evidence and candidate inspection becomes less tied to repository-only language
- operator-facing docs and serialized payloads become clearer about provider provenance

### Negative

- the radar schema and serialization layer now carry some temporary duplication
- some internal GitHub-specific semantics such as `repo_slug`-based scoring and adoption records still remain until a later slice

## Non-Goals

- this ADR does not remove `repo_slug`, `repo_name`, or `html_url`
- it does not add a second live provider
- it does not change promotion thresholds, approval policy, or experiment behavior

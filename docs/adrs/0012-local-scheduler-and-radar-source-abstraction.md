# ADR 0012: Local Scheduler Foundation And Radar Source Abstraction

- Status: Accepted
- Date: 2026-04-15

## Context

The next radar milestone needs two capabilities that were not cleanly represented in the existing code:

- a stable, tracked way to describe how local operators should schedule radar scans
- a source boundary that lets radar discovery stop depending directly on one concrete GitHub implementation

At the same time, the roadmap explicitly avoids introducing a long-running in-repo scheduler, daemon, or background queue.

## Decision

We add tracked schedule config plus a source protocol, while keeping GitHub as the only live provider for now.

Key decisions:

- define tracked schedule config in `configs/radar/schedule.yaml`
- add `skylattice radar schedule show`, `render`, and `run` as CLI-first operator surfaces
- render Windows Task Scheduler registration details instead of embedding a resident scheduler inside the repo
- introduce `RadarDiscoverySource` as the stable discovery/enrichment protocol
- keep `GitHubRadarSource` as the only live implementation in this slice
- persist provider identity in radar evidence and candidate metadata so future multi-source expansion does not require a shape break

## Consequences

Positive:

- schedule behavior is reviewable tracked config instead of hidden local glue
- radar can expand beyond GitHub later without rewriting the service boundary again
- provider identity becomes part of the durable evidence story

Tradeoffs:

- schedule rendering is Windows-first in this slice and does not yet provide parallel Linux/macOS registration helpers
- the runtime now carries a lightweight SQLite schema migration for radar evidence provider identity
- the CLI gains more scheduling surface area before a second live provider exists

## Rejected Alternatives

- add a daemon or background scheduler in the repo: rejected because it widens runtime complexity and autonomy faster than the roadmap allows
- wait to add a source abstraction until a second provider exists: rejected because provider identity and interface stability would become harder to retrofit after more radar behavior accumulates
- store schedule state only in local OS tasks: rejected because schedule intent is part of the behavior boundary and should stay reviewable in tracked config

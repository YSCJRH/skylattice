# ADR 0018: Hosted Web Control Plane And Local Agent Bridge

## Context

Skylattice already had a public docs surface plus a local-first runtime, but it did not yet have a product surface that felt like a real web application.

At the same time, the system's core thesis remained unchanged:

- execution stays local-first
- private memory stays local by default
- approvals and promotion boundaries remain explicit
- GitHub and any future hosted surface must not become runtime truth

The next product step is therefore not "move Skylattice into the cloud". It is "add a hosted control plane that can represent the product honestly while keeping the local runtime authoritative".

## Decision

Skylattice adds a dual-surface web architecture:

- GitHub Pages remains the public docs, proof, and discoverability surface
- a same-repo hosted web app becomes the authenticated product surface
- the hosted app manages identity, device pairing, command intent, and lightweight mirrored summaries
- a local Skylattice connector polls the hosted control plane and executes commands against the local runtime
- the Python runtime exposes an authenticated local bridge API for versioned web-oriented integrations, while the connector remains free to call shared service logic directly when that is the safer local path

GitHub is the first login provider for the hosted app. Personal accounts are supported, but execution still happens on user-owned local agents.

## Consequences

- Skylattice gains a real product surface without abandoning its local-first boundary
- web-triggered actions remain governed by the same local approval rules as CLI-triggered actions
- the hosted surface stores only account, pairing, command, audit, and lightweight summary state by default
- the repository now has a mixed Python and TypeScript workspace, so build and documentation surfaces must explain that split clearly
- a future production hosted rollout can move control-plane persistence to Postgres without changing the public product shape or local connector contract

---
title: Web Control Plane
description: How the hosted Skylattice app works, what stays local, and how pairing connects the browser to a local runtime without turning the cloud into runtime truth.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/web-control-plane/
jsonld: |
  {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    "name": "Skylattice Web Control Plane",
    "description": "Hosted control-plane surface for the local-first Skylattice runtime.",
    "codeRepository": "https://github.com/YSCJRH/skylattice",
    "softwareVersion": "0.4.1",
    "license": "https://github.com/YSCJRH/skylattice/blob/main/LICENSE",
    "inLanguage": "en"
  }
---

# Web Control Plane

Skylattice now has a real web-product layer, but it still keeps execution local-first.

The app is a hosted control plane for:

- GitHub sign-in
- device pairing
- control-cockpit mode, readiness, and next-action visibility
- device revocation
- onboarding and blocked-state UX
- task, radar, and memory command intent
- approval reminders and lightweight audit state
- recent task, radar, and memory outcome summaries inside each workspace
- paired-device readiness summaries derived from the latest local connector heartbeat
- lightweight mirrored summaries for browser dashboards
- pairing-state visibility so the connect flow can show active codes and already-claimed devices
- a dedicated command ledger and single-command drill-down surface in the hosted app
- scope- and status-filtered command views for task, radar, and memory troubleshooting
- dedicated device and approval pages so long-lived management work does not stay buried inside dashboard cards

It is **not** a hosted runtime. The paired local Skylattice agent still owns:

- task execution
- radar execution
- local SQLite state
- private memory
- approval and governance enforcement

## Product Shape

Skylattice now has two deliberate surfaces:

1. The public docs and proof site
2. The authenticated hosted app surface

The public docs site remains the canonical explanation and discoverability layer.

The cleanest way to think about the product now is:

- `Docs`: what the system is and why the boundary exists
- `Preview`: local read-only first-look evaluation
- `Hosted Alpha`: real sign-in, pairing, and command lifecycle
- `Local Agent`: the actual executor and governance boundary

The hosted app adds:

- a public app home
- a sign-in flow
- an optional read-only preview mode for first-look evaluation before auth and pairing
- a production-style Hosted Alpha path for real sign-in, pairing, and command lifecycle
- a dashboard shaped as a control cockpit for mode, readiness, next action, command flow, and approval pressure
- task, radar, and memory workspaces
- a connect / pairing flow
- settings for identity, pairing state, and runtime readiness

## Control Cockpit Shape

The web app is organized around the command lifecycle rather than a chat surface:

1. `Preview` shows seeded read-only command, device, pairing, and approval records.
2. `Connect` pairs a local Skylattice agent through a short-lived code.
3. `Tasks`, `Radar`, and `Memory` compose command intent only after pairing.
4. `Commands` is the central ledger for status, payload, result, error, routing, and next action.
5. The paired local agent still executes the work and enforces local governance.

Pairing and command creation also require GitHub sign-in. The app can send unpaired users to `/connect`, but creating a pairing code or live command stays disabled until the browser session is authenticated.

This keeps browser ergonomics useful without turning the hosted app into an execution substrate.

## First-Look Preview

If you only want to inspect the product shape locally before wiring OAuth, pairing, or a live connector, the web workspace also supports a read-only preview mode:

```powershell
npm install
npm run web:preview
```

That preview mode seeds representative command, device, approval, and pairing records for the guest session. It is intentionally read-only and does not turn the hosted app into runtime truth.

If you package the app through `npm run web:build` and `npm run start`, set the same preview env before the build step too, or use the repository-level wrappers:

```powershell
npm run web:preview:build
npm run web:preview:start
```

## Why Pairing Exists

The browser never needs direct localhost access in the current design.

Instead:

1. the hosted app creates a short-lived pairing code
2. the local machine claims it with `skylattice web pair`
3. a local connector stores its token under `.local/`
4. the connector polls the hosted control plane for queued commands
5. the connector executes those commands through the normal local runtime service

This keeps the browser, hosted app, and local runtime cleanly separated.

## Hosted Alpha Deployment Contract

The first real hosted target is intentionally narrow:

- `Vercel` for the public app URL
- `Neon Postgres` for hosted control-plane state
- `GitHub OAuth` for sign-in
- one or more paired local Skylattice agents per personal account

This is still a control plane, not a hosted runtime.

See the tracked deployment checklist in [ops/hosted-alpha-runbook.md](ops/hosted-alpha-runbook.md).

## What Stays Local

- private memory records
- repo contents
- local SQLite runtime state
- local governance decisions
- task and radar execution side effects

## What The Hosted App Can Store

- account identity
- paired-device metadata
- command queue records
- approval and audit summaries
- lightweight task/radar summary mirrors

The hosted app should not become a shadow memory store.

## Current Repository Surfaces

- web app workspace: [apps/web/README.md](https://github.com/YSCJRH/skylattice/tree/main/apps/web)
- Hosted Alpha env template: [apps/web/.env.example](https://github.com/YSCJRH/skylattice/blob/main/apps/web/.env.example)
- local bridge API: `src/skylattice/api/bridge.py`
- local connector commands:
  - `python -m skylattice.cli web status`
  - `python -m skylattice.cli web pair --control-plane-url <url> --code <pairing-code> --device-label "<label>"`
  - `python -m skylattice.cli web connector heartbeat`
  - `python -m skylattice.cli web connector once`

## Control-Plane Persistence

The same-repo app now has three control-plane persistence states:

- `local-file` for development
- `postgres` when `SKYLATTICE_CONTROL_PLANE_DATABASE_URL` or `DATABASE_URL` is configured
- `blocked` when Hosted Alpha semantics are active but the deployment is missing the env required for a real live app

The tracked schema is already represented through Drizzle tables, so the development backend and the hosted backend keep the same shape.

In practice:

- preview and local development can stay easy to run
- Hosted Alpha deployments fail clearly instead of pretending local-file persistence is a valid live control-plane backend
- the app shell explicitly distinguishes `Preview`, `Local development`, `Hosted Alpha blocked`, and real paired control so the browser surface cannot quietly masquerade as a public hosted runtime

## Related Pages

- [App Preview](app-preview.md)
- [Quick Start](quickstart.md)
- [Proof](proof.md)
- [Hosted Alpha Runbook](ops/hosted-alpha-runbook.md)
- [Architecture](architecture.md)
- [Governance](governance.md)

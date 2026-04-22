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
    "softwareVersion": "0.4.0",
    "license": "https://github.com/YSCJRH/skylattice/blob/main/LICENSE",
    "inLanguage": "en"
  }
---

# Web Control Plane

Skylattice now has a real web-product layer, but it still keeps execution local-first.

The app is a hosted control plane for:

- GitHub sign-in
- device pairing
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

The hosted app adds:

- a public app home
- a sign-in flow
- an optional read-only preview mode for first-look evaluation before auth and pairing
- a dashboard
- task, radar, and memory workspaces
- a connect / pairing flow
- settings for identity, pairing state, and runtime readiness

## First-Look Preview

If you only want to inspect the product shape locally before wiring OAuth, pairing, or a live connector, the web workspace also supports a read-only preview mode:

```powershell
npm install
$env:NEXT_PUBLIC_SKYLATTICE_DEMO_PREVIEW = "1"
npm run web:dev
```

That preview mode seeds representative command, device, approval, and pairing records for the guest session. It is intentionally read-only and does not turn the hosted app into runtime truth.

If you package the app through `npm run web:build` and `npm run start`, set the same preview env before the build step too, because that public preview surface is compiled into the Next.js output.

## Why Pairing Exists

The browser never needs direct localhost access in the current design.

Instead:

1. the hosted app creates a short-lived pairing code
2. the local machine claims it with `skylattice web pair`
3. a local connector stores its token under `.local/`
4. the connector polls the hosted control plane for queued commands
5. the connector executes those commands through the normal local runtime service

This keeps the browser, hosted app, and local runtime cleanly separated.

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
- local bridge API: `src/skylattice/api/bridge.py`
- local connector commands:
  - `python -m skylattice.cli web status`
  - `python -m skylattice.cli web pair --control-plane-url <url> --code <pairing-code> --device-label "<label>"`
  - `python -m skylattice.cli web connector heartbeat`
  - `python -m skylattice.cli web connector once`

## Control-Plane Persistence

The same-repo app supports two control-plane persistence modes:

- `local-file` for development
- `postgres` when `SKYLATTICE_CONTROL_PLANE_DATABASE_URL` or `DATABASE_URL` is configured

The tracked schema is already represented through Drizzle tables, so the development backend and the hosted backend keep the same shape.

## Related Pages

- [Quick Start](quickstart.md)
- [Proof](proof.md)
- [Architecture](architecture.md)
- [Governance](governance.md)

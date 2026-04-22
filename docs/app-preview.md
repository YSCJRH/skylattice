---
title: App Preview
description: Preview the Skylattice hosted app surface locally with one command, inspect the seeded read-only workspaces, and understand what changes when you move from preview to live pairing.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/app-preview/
jsonld: |
  {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    "name": "Skylattice App Preview",
    "description": "Read-only first-look entry for the Skylattice hosted app surface.",
    "codeRepository": "https://github.com/YSCJRH/skylattice",
    "softwareVersion": "0.4.0",
    "license": "https://github.com/YSCJRH/skylattice/blob/main/LICENSE",
    "inLanguage": "en"
  }
---

# App Preview

If you want to see the product-shaped web surface before wiring GitHub OAuth, pairing a local agent, or configuring a hosted deployment, start here.

## The One-Command Entry

From the repository root:

```powershell
npm install
npm run web:preview
```

Then open [http://localhost:3000/dashboard](http://localhost:3000/dashboard).

This launches the same-repo `Next.js` app in a read-only preview mode with representative data already seeded for the guest session.

## What You Can Inspect

The preview is designed to answer one question fast: does the web product surface look credible enough to keep exploring?

Open these routes first:

- `/dashboard`: paired-device status, latest commands, approval pressure, and memory activity
- `/tasks`: governed task run shape plus representative result history
- `/radar`: scan, schedule validation, replay, and rollback surfaces
- `/memory`: search, profile proposals, and review-driven memory actions
- `/commands`: command ledger and single-command drill-down
- `/connect`: pairing flow, code visibility, and claimed-device status
- `/devices` and `/approvals`: long-lived management surfaces

## What The Preview Is

- a truthful first-look entry into the hosted control-plane UX
- a seeded guest session with representative command, device, pairing, and approval records
- a way to evaluate the information architecture and interaction model before live setup

## What The Preview Is Not

- not a hosted runtime
- not a live account session
- not connected to a real local agent by default
- not allowed to queue live commands, revoke live devices, or resolve live approvals

The preview is intentionally read-only.

## What Changes In Live Mode

When you move from preview to live control, the architecture stays the same but the data becomes real:

1. sign in with GitHub
2. create a short-lived pairing code
3. claim it locally with `skylattice web pair`
4. let the local connector claim commands and report readiness

The browser still does not become runtime truth. The paired local Skylattice agent remains the executor.

## Related Pages

- [Web Control Plane](web-control-plane.md)
- [Quick Start](quickstart.md)
- [Proof](proof.md)
- [v0.4.0 Stable](releases/v0-4-0.md)

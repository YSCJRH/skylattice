# Skylattice Web App

This workspace is the hosted control-plane surface for Skylattice.

## What It Is

- public app home for product positioning and sign-in
- authenticated dashboard for paired local agents
- control-plane command queue for task, radar, and memory workflows
- pairing flow that keeps browser traffic away from localhost
- paired-device revocation and approval-reminder management from the app surface

## What It Is Not

- not a hosted runtime
- not a replacement for the Pages docs site
- not a bypass around local approvals or private memory boundaries

## Local Development

1. Install dependencies from the repository root:

```bash
npm install
```

2. Run the web app:

```bash
npm run web:dev
```

3. Optional GitHub auth env vars:

- `GITHUB_ID`
- `GITHUB_SECRET`
- `NEXTAUTH_SECRET`

4. Optional control-plane state env vars:

- `SKYLATTICE_CONTROL_PLANE_STATE_PATH`
- `SKYLATTICE_CONTROL_PLANE_DATABASE_URL`
- `DATABASE_URL`
- `SKYLATTICE_HOSTED_ALPHA`
- `NEXT_PUBLIC_SKYLATTICE_APP_URL`
- `NEXT_PUBLIC_SKYLATTICE_DOCS_URL`
- `NEXTAUTH_URL`
- `NEXT_PUBLIC_SKYLATTICE_DEMO_PREVIEW`

If you want a first-look product preview without GitHub OAuth, pairing, or a live local agent, set:

```powershell
$env:NEXT_PUBLIC_SKYLATTICE_DEMO_PREVIEW = "1"
npm run web:dev
```

That mode seeds representative read-only command, device, approval, and pairing data for the guest session so the app is inspectable before live setup.

If you do not want to remember the env var yourself, use the repository-level shortcut:

```powershell
npm run web:preview
```

For production-style `build` and `start` flows, set the same env var before `npm run web:build` as well, because the preview surface is compiled into the Next.js app at build time.

Equivalent repository-level shortcuts:

```powershell
npm run web:preview:build
npm run web:preview:start
```

If `SKYLATTICE_CONTROL_PLANE_DATABASE_URL` or `DATABASE_URL` is set, the app uses the Postgres-ready Drizzle/Neon backend instead of the local-file development store.

## Hosted Alpha Deployment Contract

The first public hosted target is:

- `Vercel` for hosting
- `Neon Postgres` for control-plane persistence
- `GitHub OAuth` for browser sign-in
- repo-local `@fontsource/*` packages so builds do not depend on live Google Fonts fetches

Use [`.env.example`](./.env.example) as the canonical env template.

Important guardrail:

- local preview and local development may use the `local-file` control-plane backend
- Hosted Alpha must use `postgres`
- if Hosted Alpha mode is active without `DATABASE_URL`, the app now enters a blocked state instead of silently falling back to local-file persistence
- the app shell now distinguishes `Preview`, `Local development`, `Hosted Alpha blocked`, and real paired control so operators do not confuse a local surface with a public deployment

That guardrail exists so a public deployment does not impersonate a credible hosted product while actually storing state in a local development JSON file.

For the tracked deployment checklist, use [Hosted Alpha Runbook](https://github.com/YSCJRH/skylattice/blob/main/docs/ops/hosted-alpha-runbook.md).

Helpful repository-level commands:

```powershell
npm run web:hosted-alpha:check
npm run web:hosted-alpha:bootstrap
npm run web:first-run:local
npm run web:cockpit:check
```

- `web:hosted-alpha:check` prints the current Hosted Alpha readiness payload and exits non-zero when required env is missing
- `web:hosted-alpha:bootstrap` applies the tracked SQL bootstrap under `apps/web/sql/hosted-alpha-bootstrap.sql` to `DATABASE_URL`
- `web:first-run:local` proves the local first-run loop: preview proof data is valid, Hosted Alpha readiness blocks as expected on localhost, the connector stays unpaired, and auth preflight reports missing live credentials without pretending local development is a live deployment
- `web:cockpit:check` starts local Next.js dev servers and checks the server-rendered UI contract for preview, blocked, local unpaired, paired-but-unauthenticated, and succeeded/failed command-detail states without exercising live Hosted Alpha sign-in

## Local Connector

Use the Python CLI from the repository root:

```bash
python -m skylattice.cli web status
python -m skylattice.cli web pair --control-plane-url http://localhost:3000 --code <pairing-code> --device-label "Primary workstation"
python -m skylattice.cli web connector once
```

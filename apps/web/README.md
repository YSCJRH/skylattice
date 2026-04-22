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
- `NEXT_PUBLIC_SKYLATTICE_APP_URL`
- `NEXT_PUBLIC_SKYLATTICE_DOCS_URL`
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

## Local Connector

Use the Python CLI from the repository root:

```bash
python -m skylattice.cli web status
python -m skylattice.cli web pair --control-plane-url http://localhost:3000 --code <pairing-code> --device-label "Primary workstation"
python -m skylattice.cli web connector once
```

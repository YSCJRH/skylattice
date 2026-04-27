# Hosted Alpha Runbook

This runbook is the tracked deployment contract for Skylattice Hosted Alpha.

## Product Boundary

Hosted Alpha means:

- a real public app URL
- GitHub browser sign-in
- real pairing codes
- a control cockpit that makes preview, blocked, unpaired, and ready states explicit
- real command queue, approvals, and device lifecycle
- a local paired Skylattice agent that still executes the work

Hosted Alpha does **not** mean:

- a hosted runtime
- multi-tenant SaaS
- browser-to-localhost direct control
- bypassing local approvals, governance, or SQLite truth

## Deployment Target

Use this stack for the first public Hosted Alpha:

- hosting: `Vercel`
- database: `Neon Postgres`
- app root: `apps/web`
- auth: `GitHub OAuth`

Preview remains a separate local/docs surface:

- `npm run web:preview`
- `npm run web:preview:check`

## Delivery Surfaces

When external project tooling is available, keep the delivery naming stable:

- GitHub public feedback/issues: use the repository issue tracker, with `#2`, `#3`, and `#4` as the initial onboarding acceptance inputs
- Linear initiative: `Hosted Alpha Launch`
- Linear epic names:
  - `Hosted App Deployment & Auth`
  - `Pairing & Device Lifecycle`
  - `Workspace Maturity`
  - `Onboarding & Trust`
  - `Alpha Launch & Feedback`
- Figma file: `Skylattice Hosted Alpha`
- Figma minimum frames:
  - public app home
  - dashboard
  - tasks
  - radar
  - memory
  - commands
  - connect
  - token/design-system mapping

If those external objects do not exist yet, this runbook remains the tracked naming source of truth.

## Required Env

See [apps/web/.env.example](https://github.com/YSCJRH/skylattice/blob/main/apps/web/.env.example) for the full template.

Required for Hosted Alpha:

- `NEXT_PUBLIC_SKYLATTICE_APP_URL`
- `NEXTAUTH_URL`
- `GITHUB_ID`
- `GITHUB_SECRET`
- `NEXTAUTH_SECRET`
- `DATABASE_URL` or `SKYLATTICE_CONTROL_PLANE_DATABASE_URL`
- `SKYLATTICE_HOSTED_ALPHA=1`

Recommended:

- `NEXT_PUBLIC_SKYLATTICE_DOCS_URL=https://yscjrh.github.io/skylattice/`

Helpful repository-level commands:

```powershell
npm run web:hosted-alpha:check
npm run web:hosted-alpha:bootstrap
npm run web:first-run:local
npm run web:cockpit:check
```

- `web:hosted-alpha:check` prints the current Hosted Alpha readiness payload and exits non-zero when blockers remain
- `web:hosted-alpha:bootstrap` applies the tracked SQL bootstrap in `apps/web/sql/hosted-alpha-bootstrap.sql` to `DATABASE_URL`
- `web:first-run:local` verifies the local blocked proof loop without pretending localhost is a live Hosted Alpha deployment
- `web:cockpit:check` verifies the local server-rendered UI contract for preview, blocked, local unpaired, paired-but-unauthenticated, and succeeded/failed command-detail states. It does not exercise live Hosted Alpha sign-in or Postgres-backed pairing.

## Important Production Guardrail

When Hosted Alpha mode is active, the app now refuses to silently fall back to local-file control-plane state.

That means:

- preview and local development may still use `local-file`
- Hosted Alpha must use `postgres`
- missing database config yields a blocked UI and `503 blocked` control-plane API responses instead of fake-success local persistence

This is intentional. A public deployment should fail clearly, not impersonate a valid multi-user hosted surface on top of a local JSON file.

## GitHub OAuth Setup

Create a GitHub OAuth app and configure:

- homepage URL: your Vercel app URL
- callback URL: `https://<your-app>/api/auth/callback/github`

The app should only advertise live sign-in once:

- the public URL is final
- OAuth callback matches that URL
- `NEXTAUTH_URL` matches the same URL

## Neon / Postgres Setup

Create a Neon Postgres database and copy the pooled connection string into:

- `DATABASE_URL`

If you want the repo to materialize the tracked tables for you, run:

```powershell
npm run web:hosted-alpha:bootstrap
```

The hosted control plane stores:

- account identity
- paired-device metadata
- pairing challenges
- command queue records
- approval reminders
- lightweight dashboard summaries

It does **not** replace:

- local runtime SQLite
- private memory
- local repo contents
- local governance truth

## Vercel Setup

Recommended project settings:

- import this repository
- set **Root Directory** to `apps/web`
- add the Hosted Alpha env vars above
- deploy after the database and OAuth callback are configured

## Release Checklist

Before calling the deployment a Hosted Alpha:

1. Open the public app URL successfully.
2. Complete GitHub sign-in.
3. Create a pairing code from the browser.
4. Claim it locally with:

```bash
python -m skylattice.cli web pair --control-plane-url <app-url> --code <pairing-code> --device-label "<label>"
```

5. Confirm `python -m skylattice.cli web connector heartbeat` updates device readiness.
6. Queue at least one command from:
   - `/tasks`
   - `/radar`
   - `/memory`
7. Confirm `/dashboard` shows the correct mode and next action.
8. Confirm command status appears in `/commands`.
9. Open one command detail page and confirm lifecycle, routing, payload, result or error, and next action are visible.
10. Revoke a device once from `/devices`.
11. Resolve an approval reminder once from `/approvals`.
12. Confirm docs still distinguish:
   - docs site
   - preview
   - live app
   - paired local agent

## Validation Notes

Record first-run proof-loop checks under `docs/ops/hosted-alpha-validations/`.

Each validation note should distinguish:

- what was verified in the current environment
- what was simulated or blocked by missing credentials, deployment resources, or pairing state
- which commands were run
- which next action would unblock the live Hosted Alpha path

When live Hosted Alpha credentials are unavailable, `npm run web:first-run:local` plus `npm run web:cockpit:check` are the repeatable local proof floor. They do not replace the live sign-in, pairing, connector heartbeat, queue, claim, result, and approval checks.

## Onboarding Acceptance Inputs

Use these GitHub issues as explicit Hosted Alpha acceptance inputs:

- `#2` first-run friction in the no-credential quick start
- `#3` comparison and use-case clarity
- `#4` onboarding feedback after stable release

Success means a cold visitor can quickly understand:

- what Skylattice is
- why preview is not the live app
- why the live app is still not a hosted runtime
- why `/commands` is the central command ledger, not a cloud execution log

## Related Pages

- [Web Control Plane](../web-control-plane.md)
- [App Preview](../app-preview.md)
- [Quick Start](../quickstart.md)
- [Architecture](../architecture.md)
- [GitHub Workflow](../github-workflow.md)

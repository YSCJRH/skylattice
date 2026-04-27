# Hosted Alpha First-Run Proof Loop Validation: 2026-04-27

## Scope

This note records the first post-cockpit proof-loop check for the Hosted Alpha control plane.

The intended loop is:

`Preview -> Sign in -> Pair local agent -> Heartbeat -> Queue command -> Connector claim -> Local execution -> Result / approval / recovery`

This run was performed from a local development shell, not a deployed Hosted Alpha environment. The goal was to separate verified local proof from credential- or deployment-blocked steps.

## Environment Summary

- branch: `codex/hosted-alpha-control-cockpit`
- app URL observed by readiness check: `http://localhost:3000`
- Hosted Alpha mode: not active
- connector pairing state: not paired
- local runtime doctor status: `ok`
- GitHub CLI state: logged in and token accessible through `gh`
- Skylattice GitHub env bridge: not configured in this shell
- OpenAI key: not configured in this shell
- Postgres control-plane database env: not configured in this shell

## Commands Run

```powershell
npm run web:hosted-alpha:check
python -m skylattice.cli web status
python -m skylattice.cli doctor auth
npm run web:preview:check
python -m skylattice.cli web connector heartbeat
npm run web:first-run:local
npm run web:cockpit:check
npm run web:connector:local
npm run web:recovery:local
npm run web:proof:local
```

## Results

### Preview Proof

`npm run web:preview:check` passed.

The preview proof state remains structurally valid:

- devices: `2`
- pairings: `2`
- commands: `6`
- approvals: `1`

This confirms the read-only first-look surface is still available before live auth, pairing, or a real local agent are configured.

`npm run web:first-run:local` now packages this local proof lane into one repeatable harness. It verifies preview data, expected local Hosted Alpha blockers, injected unpaired connector failure, and auth-preflight reporting without relying on the operator's real `.local/overrides/web-control-plane.json` pairing state.

`npm run web:cockpit:check` also passed. It starts local Next.js dev servers and checks server-rendered cockpit pages for:

- preview dashboard mode and read-only next action
- Hosted Alpha blocked dashboard and env blocker visibility
- local unpaired `/commands` CTA to pair a local agent
- paired-but-unauthenticated `/tasks` sign-in gate, while confirming the seeded connector token is not rendered
- succeeded and failed command detail pages for lifecycle, routing, payload/result/error, next safe action, and connector-token redaction

This is a local UI contract check only; it does not replace the live Hosted Alpha sign-in, Postgres-backed pairing, heartbeat, queue, claim, result, or approval checks.

`npm run web:connector:local` also passed. It starts a local Next.js control-plane server with a temporary local-file state, seeds one pairing challenge and one queued `memory.search` command for a proof user, then uses the Python connector to:

- claim the seeded pairing challenge
- write a heartbeat and auth summary
- claim the queued command over `/api/control-plane/commands/next`
- execute local `memory.search`
- record the command result through `/api/control-plane/commands/<commandId>/result`

The observed command id was `cmd-local-memory-search`, and the final command status was `succeeded`. This proves the connector protocol roundtrip locally, but it still does not prove live browser sign-in or Postgres-backed Hosted Alpha pairing creation.

`npm run web:recovery:local` also passed. It starts a local Next.js control-plane server with a temporary local-file state, seeds one pairing challenge and one queued `memory.review.confirm` command that references a missing review record, then uses the Python connector to:

- claim the seeded pairing challenge
- write a heartbeat and auth summary
- claim the queued command
- hit the expected local runtime error for `missing-review-record`
- record the command result as `failed`
- create a pending approval reminder with `repo-write` and `external-write` pressure

The observed command id was `cmd-local-recovery-proof`, and the final command status was `failed`. This proves the recovery/approval-pressure path locally, but it still does not prove live browser sign-in or a real operator approval resolution.

`npm run web:proof:local` now wraps the local proof floor in one sequential command. It runs the first-run blocked proof, server-rendered cockpit UI contract, connector success roundtrip, and connector recovery roundtrip without starting competing Next.js proof servers.

### Hosted Alpha Readiness

`npm run web:hosted-alpha:check` failed as expected in this local shell.

Observed blockers:

- `NEXT_PUBLIC_SKYLATTICE_APP_URL` still points at localhost.
- GitHub OAuth env vars are incomplete.
- `DATABASE_URL` or `SKYLATTICE_CONTROL_PLANE_DATABASE_URL` is missing.
- `NEXTAUTH_URL` is missing for hosted auth callbacks.
- Hosted Alpha mode is not active.

This is a correct blocked state. The local shell should not impersonate a real Hosted Alpha deployment.

### Connector State

`python -m skylattice.cli web status` passed and reported:

- connector config path: `.local/overrides/web-control-plane.json`
- control-plane URL: `null`
- device id: `null`
- paired: `false`
- connector token present: `false`
- bridge key env present: `false`
- local runtime doctor status: `ok`

`python -m skylattice.cli web connector heartbeat` failed as expected:

```json
{
  "status": "error",
  "error": "Connector is not paired yet. Run `python -m skylattice.cli web pair --control-plane-url <url> --code <pairing-code>` first."
}
```

This is the correct next-action failure for an unpaired local connector.

### Auth Preflight

`python -m skylattice.cli doctor auth` passed and reported:

- `gh` is available.
- `gh` is logged in.
- a GitHub token is accessible through `gh`.
- `GITHUB_TOKEN` is not exported in this shell.
- `OPENAI_API_KEY` is not configured.
- `SKYLATTICE_GITHUB_REPOSITORY` is not exported.
- repository origin suggests `YSCJRH/skylattice`, but Skylattice does not adopt it automatically.

This is consistent with the blueprint: live GitHub capability requires explicit env bridging, and task planning requires an explicit OpenAI key.

## Proof Loop Status

Verified in this run:

- preview proof data is valid
- local runtime doctor status is healthy through `web status`
- Hosted Alpha readiness fails clearly instead of falling back to local-file live semantics
- local server-rendered cockpit pages expose preview, blocked, local unpaired, paired-but-unauthenticated, and command-detail lifecycle/recovery boundaries
- the local connector can claim a seeded pairing, heartbeat, claim one command, execute local `memory.search`, and record a result through the existing HTTP control-plane API
- the local connector can record a failed command result and surface pending approval pressure through the existing HTTP control-plane API
- the local proof floor is available through one sequential command: `npm run web:proof:local`
- unpaired connector heartbeat fails with an actionable pairing instruction
- auth preflight distinguishes `gh` login from explicit Skylattice runtime credentials

Blocked in this run:

- real GitHub browser sign-in
- live pairing-code creation
- `skylattice web pair` against a public app URL
- connector heartbeat against a live control-plane URL
- queueing a live command from an authenticated browser
- connector claim and local command execution from the hosted ledger
- command result or approval recovery through `/commands`

## Next Action

The next proof-loop pass needs a real Hosted Alpha-like environment:

1. Configure a public app URL, `NEXTAUTH_URL`, GitHub OAuth, and Postgres control-plane env.
2. Run `npm run web:hosted-alpha:check` until readiness is `ready: true`.
3. Complete browser sign-in and generate a pairing code.
4. Claim the code locally with `python -m skylattice.cli web pair --control-plane-url <app-url> --code <pairing-code> --device-label "<label>"`.
5. Run `python -m skylattice.cli web connector heartbeat`.
6. Queue one low-risk command from the browser.
7. Run `python -m skylattice.cli web connector once`.
8. Inspect `/commands/<commandId>` for lifecycle, target device, payload, result or error, and next safe action.

## Boundary Notes

- This validation did not add cloud execution.
- This validation did not bypass sign-in, pairing, or connector-token requirements.
- This validation did not export or commit `.local/` state.
- This validation did not widen approval, memory, radar promotion, or self-modification semantics.

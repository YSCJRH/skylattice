# Task Brief: Hosted Alpha First-Run Proof Loop

## Intent

- Turn the Hosted Alpha control cockpit into a repeatable first-run proof loop rather than a broader web-product expansion.
- Success means a cold operator can move from preview understanding to live sign-in, pairing, connector heartbeat, command queueing, local execution, and command-result inspection without confusing the browser for runtime truth.
- The proof loop should make the current architecture legible: `Preview -> Sign in -> Pair local agent -> Heartbeat -> Queue command -> Connector claim -> Local execution -> Result / approval / recovery`.

## Constraints

- tracked artifacts likely to edit:
  - `docs/tasks/hosted-alpha-first-run-proof-loop.md`
  - `docs/ops/hosted-alpha-runbook.md`
  - `docs/web-control-plane.md`
  - `docs/app-preview.md`
  - `apps/web/**`
  - `src/skylattice/web/**`
  - `src/skylattice/api/bridge.py`
  - `tests/test_web_bridge.py`
  - `tests/test_web_cli.py`
  - `tests/test_hosted_alpha_readiness.py`
- local-only artifacts expected to change during validation:
  - `.local/state/**`
  - `.local/work/**`
  - `.local/logs/**`
  - `.local/overrides/**`
- explicit non-goals:
  - no hosted runtime execution
  - no browser-to-localhost direct control path
  - no multi-tenant SaaS runtime
  - no new command kind unless a later brief proves the existing kinds are insufficient
  - no database schema change unless first-run proof is blocked by missing lifecycle state
  - no approval, memory, radar promotion, or self-modification widening
  - no resident scheduler or background retry worker

## Affected Subsystems

- hosted web control plane: dashboard mode, connect onboarding, command center, command detail, workspace composer gates, approval/device pages
- local connector: pairing config, heartbeat, one-shot poll, command dispatch, command-result recording
- local bridge API: versioned task, radar, memory, doctor, auth, and recovery routes used by the connector path
- governance: web-triggered intent must resolve to the same local permission tiers and recovery rules as CLI-triggered runs
- docs and proof: runbook, web-control-plane docs, app preview docs, and one tracked validation note for the first-run loop
- tests and validation: web build, preview proof data, bridge/CLI/readiness tests, docs build, and manual browser checks

## Work Plan

1. Baseline the cockpit implementation.
   - Keep `/commands` as the product center and `/connect` as the onboarding path.
   - Preserve the derived UI modes: `preview`, `blocked`, `development`, `live-unpaired`, and `live-ready`.
   - Keep paired-but-unauthenticated browsers disabled for pairing and live command creation.

2. Make first-run acceptance executable.
   - Walk the checklist from the runbook in a local or Hosted Alpha-like environment.
   - Confirm GitHub sign-in, pairing-code generation, `skylattice web pair`, heartbeat, command queueing, connector claim, result recording, and command detail inspection.
   - When real Hosted Alpha env is unavailable, record exactly which steps were simulated and which were blocked by missing credentials or deployment resources.

3. Harden connector lifecycle visibility.
   - Make stale heartbeat, no heartbeat, queued-but-unclaimed, claimed, failed, succeeded, and approval-pressure states obvious from dashboard and command detail.
   - Prefer existing command fields: `createdAt`, `updatedAt`, `claimedAt`, `status`, `error`, `result`, and `deviceId`.
   - Defer schema changes unless a concrete acceptance step cannot be represented honestly.

4. Tighten recovery and approval handoff.
   - Ensure failed commands tell the user whether to inspect local logs, re-run connector heartbeat, resolve approval pressure, or retry through the local runtime.
   - Keep approval reminders as visibility, not authorization.
   - Do not add browser-side bypasses for repo-write, external-write, destructive-repo-write, memory review, or radar promotion.

5. Record proof and feedback.
   - Add tracked first-run validation notes under `docs/ops/hosted-alpha-validations/` when the proof loop is run or blocked in a meaningful way.
   - Feed onboarding issues `#2`, `#3`, and `#4` into wording and first-run friction fixes only when they map to this proof loop.
   - Keep one-time operator observations separate from durable docs and rules.

## Verification

- automated checks:
  - `npm run web:preview:check`
  - `npm run web:first-run:local`
  - `npm run web:build`
  - `python -m pytest tests/test_web_bridge.py tests/test_web_cli.py tests/test_hosted_alpha_readiness.py -q`
  - `python -m mkdocs build --strict`
- optional broader checks before release framing:
  - `python -m pytest -q`
  - `python -m compileall src/skylattice`
  - `python -m skylattice.cli doctor`
  - `python tools/run_validation_suite.py`
- manual first-run checks:
  - preview clearly says it is read-only sample data
  - blocked Hosted Alpha clearly points to deployment env blockers
  - unauthenticated paired browser cannot queue live commands or create pairing codes
  - unpaired live browser routes users to `/connect`
  - paired and authenticated browser can queue a command intent
  - local connector can heartbeat, claim one command, execute locally, and record result or failure
  - `/commands` and command detail show lifecycle, target device, payload, result/error, and next safe action

## Acceptance Criteria

- A cold operator can explain in one sentence why the browser is a control cockpit and not a hosted runtime.
- No live composer suggests execution before sign-in and local pairing are both ready.
- The connector path can be validated with one command and one result record without adding a new workflow.
- Every first-run failure mode has a next action: sign in, configure Hosted Alpha env, pair local agent, run heartbeat, inspect local runtime failure, or resolve local approval pressure.
- The proof loop leaves an auditable trail in tests, docs, and optionally an ops validation note, not just chat history.

## Notes

- This is the recommended post-cockpit wedge because it aligns Phase 5 operational proof with ADR 0018's hosted-control-plane boundary.
- The first blocked local proof-loop note is `docs/ops/hosted-alpha-validations/2026-04-27-first-run-proof-loop.md`.
- The local harness command is `npm run web:first-run:local`; it verifies preview proof data, local Hosted Alpha blocked readiness, unpaired connector failure, and auth-preflight reporting without pretending to be a live deployment.
- The work should stay narrow. If the first-run proof reveals a need for schema evolution, auth-provider expansion, or new command kinds, create a separate brief before implementation.
- The highest-cost mistake is making the hosted app appear more authoritative than the local runtime. Favor disabled states, explicit blockers, and local recovery guidance over optimistic UI.

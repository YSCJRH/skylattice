# Task Brief: Hosted Alpha Control Cockpit

## Intent

- Move the same-repo web app from a credible Hosted Alpha demo toward a control cockpit for paired local Skylattice agents.
- Success means a cold user can quickly identify whether the app is in preview, blocked, unpaired, local development, or paired-ready mode, then follow the correct next action without mistaking the browser for runtime truth.

## Constraints

- tracked artifacts to edit: `apps/web/**`, `docs/app-preview.md`, `docs/web-control-plane.md`, `docs/ops/hosted-alpha-runbook.md`, `docs/tasks/hosted-alpha-control-cockpit.md`
- local-only artifacts expected to change: possible build or test caches only
- explicit non-goals: no database schema change, no new command kind, no hosted runtime, no browser-to-localhost direct control, no cloud execution path, no governance bypass

## Affected Subsystems

- hosted web app: derived control-plane mode, dashboard cockpit, command center, connect onboarding, and workspace command gates
- control-plane docs: preview/live/local-agent framing and Hosted Alpha release checklist
- governance boundary: preserve the rule that web-triggered intent resolves back to the same local runtime approvals
- connector flow: keep pairing and connector heartbeat as the bridge between browser state and local execution readiness

## Verification

- `npm run web:preview:check`
- `npm run web:build`
- `python -m pytest tests/test_web_bridge.py tests/test_web_cli.py tests/test_hosted_alpha_readiness.py -q`
- `python -m mkdocs build --strict`
- manual review of preview, blocked, unpaired, and paired-ready states when the corresponding environments are available

## Notes

- The implementation adds only a front-end derived `ControlPlaneMode`; persisted control-plane records keep the existing shape.
- `/commands` is the product center for command lifecycle inspection: queued intent, connector claim, local result, failure, approval pressure, and next action.
- `/connect` is the live onboarding path whenever the app has no paired local executor.
- task, radar, and memory workspaces remain command composers. They do not execute work directly and stay disabled in preview, blocked, unpaired, and unauthenticated paired states.
- The browser can improve visibility and ergonomics, but local SQLite state, private memory, execution, and governance remain owned by the paired local runtime.

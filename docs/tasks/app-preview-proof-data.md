# Task Brief: App Preview Proof Data

## Intent

- make the hosted app preview state inspectable as a tracked redacted proof artifact instead of leaving it only in TypeScript seed code
- success means the app preview, docs, and proof surfaces all point to the same tracked JSON sample for representative command, device, pairing, and approval records

## Constraints

- tracked artifacts to edit:
  - `examples/redacted/*`
  - `apps/web/lib/control-plane/demo.ts`
  - `docs/app-preview.md`
  - `docs/proof.md`
  - `tests/test_public_readiness.py`
- local-only artifacts expected to change:
  - none
- explicit non-goals:
  - no live data export from `.local/`
  - no hosted runtime claim
  - no new preview behavior beyond using tracked proof data as the seed source

## Affected Subsystems

- hosted app preview seed data
- public proof artifacts
- app preview documentation

## Verification

- `npm run web:build`
- `python -m pytest tests/test_public_readiness.py -q`
- `python -m mkdocs build --strict`
- manual checks:
  - the app preview still builds with the tracked proof data source
  - the new JSON is linked from docs
  - the JSON contains no local paths, secrets, or non-public state

## Notes

- assumption: tracked proof data is more durable than code-only seed values for both maintainers and external evaluators
- risk: avoid drifting field names away from the actual control-plane shapes used in the app
- follow-up: if the preview model grows, consider adding a tiny export/check tool that validates the JSON shape explicitly

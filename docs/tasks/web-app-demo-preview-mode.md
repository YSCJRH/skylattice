# Task Brief: Web App Demo Preview Mode

## Intent

- give the hosted web control plane a truthful first-look entry for unauthenticated visitors and local evaluators
- success means `apps/web` can render representative dashboard, task, radar, memory, device, approval, and command surfaces in a read-only preview mode without requiring GitHub OAuth, pairing, or a live local agent first

## Constraints

- tracked artifacts to edit:
  - `apps/web/**`
  - `README.md`
  - `docs/web-control-plane.md`
  - `apps/web/README.md`
- local-only artifacts expected to change:
  - none required
- explicit non-goals:
  - no new hosted runtime behavior
  - no new permission tier
  - no production deployment work
  - no browser-to-localhost direct RPC

## Affected Subsystems

- hosted web control plane
- control-plane store abstraction
- product onboarding and preview UX
- public docs for the web product surface

## Verification

- `npm run web:lint`
- `npm run web:build`
- `python -m pytest -q`
- `python -m mkdocs build --strict`
- manual check:
  - guest preview mode shows representative read-only data instead of only empty states
  - mutating guest actions stay blocked
  - docs explain how to enable the local preview path honestly

## Notes

- assumption: the highest-value next productization step is reducing first-view friction, not widening execution capability
- risk: demo data must stay clearly labeled as representative preview data so it cannot be mistaken for live runtime truth
- follow-up: if the app gets a real hosted deployment URL later, the same preview mode can act as the public pre-sign-in tour

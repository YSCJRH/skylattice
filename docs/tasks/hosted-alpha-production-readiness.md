# Task Brief: Hosted Alpha Production Readiness

## Intent

- harden the hosted web control plane so production-like deployments behave like a real Hosted Alpha instead of silently falling back to local development behavior
- success means hosted deployments require Postgres-backed control-plane state, app surfaces clearly distinguish live vs preview mode, and the repo contains a concrete Vercel/Neon/GitHub OAuth deployment runbook

## Constraints

- tracked artifacts to edit:
  - `apps/web/**`
  - `README.md`
  - `docs/web-control-plane.md`
  - `docs/github-workflow.md`
  - `docs/architecture.md`
  - `tests/test_public_readiness.py`
  - `.github/workflows/ci.yml` only if validation coverage needs alignment
- local-only artifacts expected to change:
  - none required
- explicit non-goals:
  - no multi-tenant SaaS model
  - no hosted runtime execution
  - no browser-to-localhost direct control path

## Affected Subsystems

- hosted web control plane
- control-plane persistence selection
- hosted alpha deployment and operations
- public product positioning

## Verification

- `npm run web:lint`
- `npm run web:build`
- `python tools/check_web_preview_state.py`
- `python -m pytest -q`
- `python -m mkdocs build --strict`
- manual checks:
  - production-like config no longer falls back to local-file persistence
  - preview and live entry states are visibly distinct in the app UI
  - deployment docs are decision-complete for Vercel + Neon + GitHub OAuth

## Notes

- assumption: the first Hosted Alpha target is `Vercel + Neon + GitHub OAuth`, while local preview remains a first-look path
- risk: production misconfiguration should fail clearly, not degrade into a local-dev control-plane mode that looks successful
- follow-up: actual Figma and Linear object creation may still require manual setup if live plugin resources remain unavailable in this environment

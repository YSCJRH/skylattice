# Web Product Upgrade

## Intent

- evolve Skylattice from a docs-first repo with a local CLI/runtime into a dual-surface product with a hosted web control plane
- succeed when the repository contains a same-repo web app foundation, a governed local bridge path, and an inspectable connector flow that keeps execution local-first

## Constraints

- tracked artifacts to edit: `README.md`, `docs/architecture.md`, `docs/governance.md`, `docs/github-workflow.md`, `docs/adrs/*.md`, `apps/web/**`, `src/skylattice/api/**`, `src/skylattice/web/**`, tests, root workspace metadata, and CI if web build validation is added
- local-only artifacts expected to change: `.local/state/*`, `.local/overrides/*`, and any local control-plane state created by connector or development workflows
- explicit non-goals: no hosted multi-tenant runtime, no browser-to-localhost direct control path, no silent approval bypass, no replacement of the Pages docs surface, and no removal of the existing CLI

## Affected Subsystems

- kernel
- actions
- governance
- ledger
- memory
- planning
- evolution

## Verification

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- `python -m skylattice.cli web status`
- `npm run web:build`
- `python -m mkdocs build --strict`
- manual checks for public app home, dashboard shells, pairing flow scaffolding, and docs/app cross-link integrity

## Notes

- default hosted control-plane persistence may start with a local-file development backend while the tracked schema and interfaces stay Postgres-ready
- GitHub remains the first login provider and an external collaboration surface, not runtime truth
- web-triggered operations must still flow through the same local governance and approval gates as CLI-triggered operations

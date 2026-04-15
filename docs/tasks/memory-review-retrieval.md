# Memory Review And Retrieval

## Intent

- turn Skylattice memory into an operator-reviewed local subsystem instead of a write-only audit trail
- feed ranked memory context into task planning without widening runtime permissions or making the API mutable

## Constraints

- tracked artifacts to edit: memory/runtime/API/CLI code, docs, ADRs, tests
- local-only artifacts expected to change: `.local/state/**`, `.local/memory/exports/**`
- explicit non-goals: no scheduler, no vector database, no browser automation, no radar scoring change, no write API

## Affected Subsystems

- memory
- runtime
- planning
- api
- docs

## Verification

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- manual check that `.local/` exports remain untracked

## Notes

- reuse `memory_records` and activate `RecordStatus.CONSTRAINED` for review proposals
- keep the milestone CLI-first and local-first

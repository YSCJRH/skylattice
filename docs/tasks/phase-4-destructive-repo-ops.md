# Phase 4 Brief: Explicit Destructive Repo Ops

## Intent

- Add tightly scoped destructive tracked-file primitives for task-agent runs: `delete_file` and `move_file`.
- Keep destructive repo lifecycle changes deny-by-default unless the operator explicitly grants a separate destructive repo approval.
- Success means task plans can express destructive file lifecycle intent, runtime can execute and verify those steps deterministically, and recovery surfaces clearly say when destructive approval is required.

## Constraints

- Tracked artifacts to edit:
  - `src/skylattice/actions/repo.py`
  - `src/skylattice/governance/service.py`
  - `src/skylattice/runtime/service.py`
  - `src/skylattice/runtime/models.py`
  - `src/skylattice/planning/service.py`
  - `src/skylattice/providers/openai.py`
  - `src/skylattice/cli.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/governance.md`
  - `docs/roadmap.md`
  - `docs/adrs/`
  - `tests/test_smoke.py`
  - `tests/test_public_readiness.py`
- Local-only artifacts expected to change:
  - `.local/state/skylattice.sqlite3` during verification
- Explicit non-goals:
  - no directory delete or move support
  - no background cleanup worker or automatic destructive mutation
  - no widening of GitHub write behavior, approval tiers for external actions, or validation shell scope

## Affected Subsystems

- actions
- planning
- governance
- runtime
- ledger

## Verification

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- `python -m mkdocs build --strict`
- manual doc consistency check for destructive approval wording and recovery guidance

## Notes

- The current runtime already supports richer non-destructive primitives, so the missing boundary is not expressiveness but audited destructive approval semantics.
- A separate destructive approval keeps `repo-write` meaningful without turning every tracked write approval into blanket permission for delete or move.

# Task-Agent vNext Public Baseline

## Intent

- Upgrade the task-agent from full-file rewrite bias to deterministic text-edit execution for small repo tasks.
- Establish a Windows-first public engineering baseline with tracked validation config, GitHub CI, and review templates.
- Success means task runs can execute `rewrite`, `replace_text`, `insert_after`, and `append_text`; validation commands come from tracked config; the repo exposes minimum CI and PR/Issue hygiene; and docs stay aligned with the new boundary.

## Constraints

- Tracked artifacts to edit: `README.md`, `docs/architecture.md`, `docs/governance.md`, `docs/github-workflow.md`, `CONTRIBUTING.md`, `prompts/system/planner.md`, `docs/adrs/0004-deterministic-text-edit-primitives.md`, `configs/task/validation.yaml`, `.github/**`, runtime/provider/tests under `src/` and `tests/`.
- Local-only artifacts expected to change: `.local/state/skylattice.sqlite3` and transient test caches during verification.
- Explicit non-goals: no radar feature expansion, no cross-platform runtime rewrite, no review-thread automation, no scheduler work.

## Affected Subsystems

- planning
- actions
- runtime
- governance
- ledger
- prompts
- docs

## Verification

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- `python tools/run_validation_suite.py`
- Manual doc consistency check across README, architecture, governance, GitHub workflow, ADR, and task brief.

## Notes

- The tracked validation config is the shared source of truth for task-agent checks and GitHub Actions CI.
- Deterministic text-edit primitives are intentionally text-native and do not introduce AST-based rewriting or arbitrary shell execution.
- Windows-first support is explicit for this milestone; broader platform support remains future work.

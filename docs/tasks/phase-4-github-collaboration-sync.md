# Phase 4 Brief: GitHub Collaboration Sync Hardening

## Intent

- Make GitHub collaboration steps more explicit, inspectable, and recovery-safe before moving on to broader automation.
- Focus the next milestone on the task-agent tail where local work crosses into remote collaboration: draft PR sync and related issue-comment coordination.
- Success means PR sync no longer behaves like a single opaque external-write step: the runtime can preflight relevant remote state, record the actual sync target, and surface clearer recovery guidance when collaboration state has changed.

## Constraints

- Tracked artifacts to edit:
  - `src/skylattice/actions/github.py`
  - `src/skylattice/runtime/service.py`
  - `src/skylattice/cli.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/github-workflow.md`
  - `docs/roadmap.md`
  - `docs/adrs/`
  - `tests/test_smoke.py`
  - `tests/test_public_readiness.py`
- Local-only artifacts expected to change:
  - `.local/state/skylattice.sqlite3` during verification
- Explicit non-goals:
  - no review-thread automation
  - no issue creation workflow expansion
  - no merge, close, reopen, label, or force-push automation
  - no background sync worker and no GitHub state mirroring into local runtime truth

## Affected Subsystems

- actions
- runtime
- governance
- ledger
- docs

## Verification

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- `python -m mkdocs build --strict`
- manual check that docs describe GitHub as a collaboration and audit layer rather than runtime truth

## Notes

- The system already has bounded `github_context`, branch-scoped draft PR reuse, and issue-comment preflight.
- The remaining gap is operator trust at the remote boundary: when a sync step is blocked, retried, or resumed, Skylattice should say exactly which remote target it expects, what it found, and why resuming is or is not safe.
- A good next slice likely includes PR-target inspection, richer sync metadata in `task inspect`, and better recovery language for remote collaboration steps without widening autonomy.

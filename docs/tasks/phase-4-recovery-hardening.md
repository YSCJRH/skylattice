# Phase 4 Brief: Task Recovery And Sync Hardening

## Intent

- Make the next milestone a narrow Phase 4 slice focused on halted-run recovery, retry safety, and GitHub sync hardening.
- Success means Skylattice can resume interrupted task runs with clearer diagnostics and lower duplicate-side-effect risk before we widen the action surface further.

## Constraints

- Tracked artifacts to edit:
  - `src/skylattice/runtime/`
  - `src/skylattice/actions/`
  - `src/skylattice/api/`
  - `src/skylattice/cli.py`
  - `docs/architecture.md`
  - `docs/governance.md`
  - `docs/github-workflow.md`
  - `docs/roadmap.md`
  - relevant ADRs
- Local-only artifacts expected to change:
  - `.local/state/skylattice.sqlite3`
  - `.local/work/`
  - `.local/logs/`
- Explicit non-goals:
  - no scheduler or background recovery worker
  - no arbitrary shell execution expansion
  - no AST edit pipeline
  - no review-thread automation
  - no broader radar scoring changes

## Affected Subsystems

- runtime
- actions
- governance
- ledger
- GitHub collaboration surfaces

## Verification

- tests for rerunning halted repo-write and external-write steps without duplicate PR or issue-comment side effects
- tests for inspect surfaces exposing recovery metadata and next-step guidance
- smoke coverage for resume flows after failed push or GitHub sync steps
- manual doc consistency check across architecture, governance, and GitHub workflow docs

## Notes

- Why this is next:
  - the blueprint emphasizes reversibility, explicit approvals, and GitHub as an audit surface rather than runtime truth
  - memory retrieval is now live in planning, so stronger recovery behavior matters more than widening task autonomy
  - current deterministic text edits are good enough for another iteration; recovery and diagnostics are the sharper risk
- Recommended slice order:
  1. record retry and recovery metadata on run steps and in `task inspect`
  2. make PR sync and issue-comment steps idempotent or deduplicated on resume
  3. improve halted-run diagnostics and operator guidance in CLI/API surfaces
  4. only then evaluate richer repo operations or safer command envelopes as the next Phase 4 slice
- Follow-up slices after this brief:
  - richer repo operations such as explicit create/move/delete primitives
  - safer command execution envelopes with tracked allowlists
  - better issue and PR planning context synchronization

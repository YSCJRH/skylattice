# Task Brief: Auth Capability Preflight

## Intent

- Turn the current GitHub and OpenAI environment blockers into a safe, explicit, read-only diagnostic flow instead of a scattered set of runtime failures.
- Success means an operator can tell, from one read-only CLI surface, whether `gh` is logged in, whether Skylattice runtime credentials are explicitly configured, whether a repo hint is present or inferable, and which live capabilities remain blocked.

## Constraints

- tracked artifacts to edit: `docs/tasks/auth-capability-preflight.md`, `src/skylattice/cli.py`, `src/skylattice/runtime/service.py`, `src/skylattice/actions/github.py`, `tools/run_authenticated_smoke.py`, selected docs under `README.md` and `docs/`, and tests covering CLI, adapter diagnostics, and public readiness
- local-only artifacts expected to change: `.local/state/**`, disposable validation clones, and clone-local safe-validation overrides
- explicit non-goals: no automatic credential adoption from `gh`, no silent repo-hint adoption from `origin`, no live radar promotion in the primary checkout, no API route changes, no governance widening

## Affected Subsystems

- CLI diagnostics and helper surfaces
- GitHub adapter initialization and local auth diagnostics
- runtime capability reporting
- authenticated smoke guidance
- operator docs for token-enabled setup and safe weekly validation

## Verification

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- `python -m skylattice.cli doctor auth`
- `python -m skylattice.cli doctor github-bridge --format json`
- `python tools/run_validation_suite.py`
- `python -m mkdocs build --strict`
- disposable-clone safe validation run with explicit bridge and clone-local no-promotion override

## Notes

- `gh auth` may be used as an explicit bridge source, but Skylattice runtime should never consume it automatically
- repo slug inference from `origin` is for operator confirmation only; runtime enablement still requires explicit configuration
- safe-validation remains the only acceptable validation path for `radar schedule run` during this work

# Task Brief: Phase 5 Operational Closure

## Intent

- Close the next release cycle around Phase 5 operational closure instead of new capability expansion.
- Success means Skylattice has a repeatable weekly radar validation loop, tracked prompt files own the human-readable provider instructions, and release-facing validation results are recorded honestly when credentials are unavailable.

## Constraints

- tracked artifacts to edit: `docs/tasks/phase-5-operational-closure.md`, `docs/tasks/phase-5-decision-frame.md`, `docs/radar-scheduling.md`, `docs/ops/radar-weekly-validation-template.md`, `docs/ops/radar-validations/*`, `docs/architecture.md`, prompt files under `prompts/system/`, `src/skylattice/providers/openai.py`, and provider tests
- local-only artifacts expected to change: sibling or isolated validation clones, `.local/radar/validations/**`, and optional credentialed smoke outputs
- explicit non-goals: no second live radar provider, no CLI/API surface expansion, no governance widening, no benchmark branch revival, no AST-aware task edits

## Affected Subsystems

- Phase 5 release framing and maintainer decision surfaces
- radar scheduling runbook and weekly validation records
- tracked prompt assets under `prompts/system/`
- `OpenAIProvider` prompt construction and provider tests

## Verification

- `python -m pytest -q`
- `python -m compileall src/skylattice`
- `python -m skylattice.cli doctor`
- `python -m skylattice.cli doctor auth`
- `python -m skylattice.cli doctor github-bridge --format json`
- `python tools/run_validation_suite.py`
- `python -m mkdocs build --strict`
- `git diff --check`
- `python tools/run_authenticated_smoke.py --provider github` only when `GITHUB_TOKEN` is configured
- `python tools/run_authenticated_smoke.py --provider openai` only when `OPENAI_API_KEY` is configured

## Notes

- safe weekly validation mode should use a disposable validation clone plus a local no-promotion override inside that clone
- live promotion-capable mode remains a separate operator path and should not be exercised accidentally from the validation environment
- auth-dependent validation that cannot run in the current environment must be recorded as skipped or blocked, never as passed

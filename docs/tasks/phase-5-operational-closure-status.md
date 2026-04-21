# Phase 5 Operational Closure Status

Date: 2026-04-21

## Decision

- keep the next release-defining story on Phase 5 operational closure rather than a broader capability wedge
- treat onboarding issues `#2`, `#3`, and `#4` as supporting signal for wording and first-run clarity, not as closeout gates

## Satisfied Now

- the weekly safe-validation path has two tracked notes under `docs/ops/radar-validations/2026-04-16-weekly-github.md` and `docs/ops/radar-validations/2026-04-17-weekly-github.md`, so the proof loop is no longer represented by one isolated pass
- the scheduling runbook now distinguishes safe validation from the live promotion-capable path and the weekly record template now captures trigger method, runtime environment, promotion capability, credential prerequisites, and manual intervention points
- `prompts/system/` now owns the human-readable OpenAI provider instructions; runtime code keeps interpolation, missing-prompt checks, JSON-schema constraints, response parsing, and edit-mode enforcement only
- the required local closeout checks passed on 2026-04-21: `python tools/run_validation_suite.py` passed and `python -m mkdocs build --strict` completed successfully
- the current auth picture is explicit: `python -m skylattice.cli doctor auth` shows GitHub can be bridged from `gh`, while `OPENAI_API_KEY` is still absent from the shell by default
- the GitHub authenticated smoke path is proven as read-only and explicit: on 2026-04-21, `python tools/run_authenticated_smoke.py --provider github` passed after bridging `GITHUB_TOKEN` and `SKYLATTICE_GITHUB_REPOSITORY` into the shell

## Remaining Before Close

- a separate live promotion-capable operator pass is still intentionally distinct from the safe weekly proof path and should stay that way unless it is scheduled as a deliberate exercise
- the OpenAI authenticated smoke remains blocked until `OPENAI_API_KEY` is configured explicitly
- release-facing validation still depends on maintainers recording blocked or skipped auth checks honestly whenever the current shell is not fully provisioned

## Explicitly Deferred

- second live radar provider
- resident scheduler or daemon
- AST-aware task edits
- autonomy or permission widening

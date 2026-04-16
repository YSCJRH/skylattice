# Task Brief: Authenticated Smoke Validation

## Intent

- Add an opt-in, read-only smoke validation lane for live GitHub and OpenAI connectivity without widening the default tracked validation baseline.
- Success means operators can run one command to verify their authenticated adapters work, while the default `doctor` and CI path remain zero-credential and stable.

## Constraints

- tracked artifacts to edit: `docs/tasks/authenticated-smoke-validation.md`, `tools/run_authenticated_smoke.py`, `src/skylattice/actions/github.py`, `src/skylattice/providers/openai.py`, `README.md`, `docs/architecture.md`, `tests/test_actions_github.py`, `tests/test_provider.py`, `tests/test_public_readiness.py`
- local-only artifacts expected to change: none
- explicit non-goals: no default CI change, no automatic credential use in `doctor`, no write operations against GitHub, no repo mutation, no prompt or governance expansion

## Affected Subsystems

- GitHub adapter read-only connectivity path
- OpenAI provider read-only connectivity path
- operator tooling under `tools/`
- public operator-facing docs and public-readiness expectations

## Verification

- `python -m pytest tests/test_actions_github.py -q`
- `python -m pytest tests/test_provider.py -q`
- `python -m pytest tests/test_public_readiness.py -q`
- `python -m compileall src/skylattice`
- `git diff --check`

## Notes

- the tool should fail clearly when the selected provider lacks required credentials
- the tool should emit JSON so operators can compare local results and automation can consume it later if needed
- the default validation profile remains intentionally credential-free

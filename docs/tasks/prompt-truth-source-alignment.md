# Task Brief: Prompt Truth-Source Alignment

## Intent

- Reduce prompt drift by making the tracked prompt files in `prompts/system/` part of the runtime path used by `OpenAIProvider`.
- Success means the runtime no longer relies only on Python string literals for core planner instructions, and the remaining split between tracked prompt intent and code-level scaffolding is explicit.

## Constraints

- tracked artifacts to edit: `docs/tasks/prompt-truth-source-alignment.md`, `src/skylattice/providers/openai.py`, `docs/architecture.md`, `tests/test_provider.py`
- local-only artifacts expected to change: none
- explicit non-goals: no prompt-behavior rewrite, no new reflection runtime, no provider API expansion beyond the current OpenAI path, no governance change

## Affected Subsystems

- tracked prompt assets under `prompts/system/`
- `OpenAIProvider` prompt construction
- maintainer-facing architecture notes about prompt truth sources
- provider-level tests

## Verification

- `python -m pytest tests/test_provider.py -q`
- `python -m pytest tests/test_public_readiness.py -q`
- `git diff --check`

## Notes

- recommended split: tracked files provide stable mission and planner intent, while runtime code continues to provide operation-specific scaffolding and JSON-schema constraints
- `reflector.md` stays tracked but unused until a real reflection path exists

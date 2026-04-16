# Task Brief: Onboarding Clarity Pass

## Intent

- Reduce first-run hesitation by making the no-credential path, token-enabled path, and current product boundaries easier to understand on the first read.
- Success means a cold visitor can answer three questions faster: what Skylattice proves without credentials, what still requires real tokens, and whether Skylattice is the right category of tool for their needs.

## Constraints

- tracked artifacts to edit: `docs/tasks/onboarding-clarity-pass.md`, `docs/quickstart.md`, `docs/use-cases.md`, `docs/comparison.md`, `docs/faq.md`
- local-only artifacts expected to change: none
- explicit non-goals: no runtime code changes, no roadmap change, no new public claims about external adoption, no broad rewrite of the overall release story

## Affected Subsystems

- zero-credential onboarding path
- token-enabled workflow explanation
- use-case positioning
- category comparison and FAQ clarity

## Verification

- `python -m pytest tests/test_public_readiness.py -q`
- `python -m mkdocs build --strict`
- `git diff --check`

## Notes

- this pass is meant to sharpen first-pass comprehension, not to invent external feedback that the repo does not actually have
- the highest-signal friction points from issues `#2`, `#3`, and `#4` are: unclear proof boundaries, unclear difference between no-token and token-enabled flows, and slow understanding of where Skylattice fits

# Cover Refresh

## Intent

- redesign the GitHub social preview and the README/Pages hero in a premium systems direction
- success means the repo first screen feels more memorable, the social preview reads at thumbnail size, and the new assets are tracked in both the repo and Figma

## Constraints

- tracked artifacts to edit: `README.md`, `docs/index.md`, `docs/assets/social-preview.svg`, `docs/assets/social-preview.png`, `docs/assets/cover-hero.svg`, `tests/test_public_readiness.py`
- local-only artifacts expected to change: local Figma draft file `Skylattice Cover Refresh`
- explicit non-goals: no product copy rewrite beyond first-screen packaging, no runtime behavior changes, no hidden repo setting changes that cannot be represented in tracked assets

## Affected Subsystems

- docs
- public surfaces
- discoverability

## Verification

- `python -m pytest tests/test_public_readiness.py -q`
- `python -m mkdocs build --strict`
- manual check of README first screen and Pages homepage hero
- confirm `docs/assets/social-preview.png` is under 1 MB and sized for GitHub social preview

## Notes

- use one shared visual system across the social preview and README hero
- keep the design grounded in local-first, governed, Git-native positioning rather than generic AI product aesthetics

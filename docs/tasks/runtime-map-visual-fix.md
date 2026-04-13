# Runtime Map Visual Fix

## Intent

- fix text overflow in the public runtime architecture image shown on the repository homepage
- success means `docs/assets/runtime-architecture.svg` renders without text escaping cards or the outer canvas at GitHub README scale

## Constraints

- tracked artifacts to edit: `docs/assets/runtime-architecture.svg`, public-readiness tests if useful
- local-only artifacts expected to change: `.local/visual-check/**`
- explicit non-goals: no architecture semantics change, no README content rewrite, no runtime behavior change

## Affected Subsystems

- docs
- public surfaces

## Verification

- render the SVG locally and inspect a screenshot
- `python -m pytest tests/test_public_readiness.py -q`
- `python -m mkdocs build --strict`

## Notes

- the issue is SVG text layout, not GitHub Markdown image sizing
- long labels should be wrapped into explicit `tspan` lines instead of relying on browser wrapping

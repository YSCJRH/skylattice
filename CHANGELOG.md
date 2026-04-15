# Changelog

## v0.3.0 - Stable Phase 4 Closeout And Phase 5 Entry

Date: 2026-04-15

### Added

- GitHub collaboration sync hardening with branch-scoped PR preflight, richer PR sync result payloads, and recovery summaries that surface remote target metadata
- tracked radar schedule config plus Windows-first `radar schedule show`, `render`, and `run` operator surfaces
- a stable radar discovery source protocol and provider-tagged radar evidence for future multi-source expansion
- ADRs for GitHub collaboration sync hardening and local scheduler plus radar source abstraction
- `v0.3.0 Stable` release notes and Pages release surface

### Changed

- the canonical stable release signal now points to `v0.3.0 Stable`
- README, Pages landing pages, AI distribution docs, llms files, sitemap, and citation metadata now align on `v0.3.0`
- roadmap status now treats Phase 4 as complete and Phase 5 as in progress

### Notes

- `v0.2.2 Stable` remains part of the public history as the external authority kit release
- this release does not introduce a resident scheduler, daemon, or second live radar source
- GitHub remains a collaboration and audit layer rather than runtime truth

## v0.2.2 - Stable External Authority Kit

Date: 2026-04-10

### Added

- a stable `v0.2.2` release surface for the external authority kit across the package metadata, Pages release page, and release notes source
- a 30-day external authority program, reusable directory blurbs, and a posting runbook under `docs/outreach/`
- a post-release review summary documenting the current discoverability bottlenecks after the stable baseline launch

### Changed

- the canonical stable release signal now points to `v0.2.2 Stable`
- README, Pages landing pages, AI distribution ops, llms files, sitemap, and outreach assets now link to the `v0.2.2` stable release page
- the stable release story now frames this cut as a discoverability and authority follow-up rather than a runtime expansion

### Notes

- `v0.2.1 Stable` remains part of the public history as the first stable baseline
- this release does not add new runtime APIs or execution behavior; it packages the authority-building layer for outward-facing distribution
## v0.2.1 - Stable Discoverability Baseline

Date: 2026-04-09

### Added

- a first non-pre-release stable release surface for Skylattice across the package metadata, Pages release page, and release notes source
- answer-first English landing pages for `what-is`, `quickstart`, `comparison`, `faq`, and `proof`
- clean UTF-8 Chinese mirror pages for the high-value public surfaces under `docs/zh/`
- outreach assets for launch posts, comparison posts, distribution targets, and community post drafts
- tracked AI-search review summaries under `evals/ai-search/`

### Changed

- the public release story now centers on `v0.2.1 Stable` instead of only the `v0.2.0` public preview
- `mkdocs.yml`, `llms.txt`, `llms-full.txt`, and `sitemap.xml` now point to the stable release and expanded discoverability assets
- `docs/ai-distribution-ops.md` and `docs/ai-search-benchmark.md` now document a weekly four-agent review loop instead of a single-thread benchmark posture
- README and overview surfaces now describe Skylattice as an early-stage runtime with a stable public baseline

### Notes

- `v0.2.0 Public Preview` remains part of the public history but is no longer the primary release signal
- remote follow-up still includes publishing the stable GitHub release, confirming the custom social preview image, and completing Search Console / Bing verification

## v0.2.0 - Public Preview

Date: 2026-04-09

### Added

- a conversion-first README with clearer positioning, why-star framing, quick-start paths, and proof assets
- redacted sample outputs for `doctor`, `task inspect`, and `radar inspect`
- public use-case and comparison pages to clarify where Skylattice fits
- tracked release notes for the first public preview under `docs/releases/`
- SVG proof assets for runtime health, task and radar workflows, and architecture

### Changed

- package metadata now uses a search-friendlier description aligned with the public positioning
- architecture docs now link directly to the public runtime diagram and README proof surfaces

### Notes

- `v0.2.0 Public Preview` has been published as a GitHub pre-release
- GitHub repository description and topics have been aligned with the public positioning

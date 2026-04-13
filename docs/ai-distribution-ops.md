---
title: AI Distribution Ops
description: Operational checklist for keeping Skylattice public pages, metadata, stable releases, and weekly discoverability reviews aligned.
robots: noindex, follow
---

# AI Distribution Ops

Use this checklist whenever the public positioning, site structure, or release posture changes.

## Source Of Truth Surfaces

Keep these public pages aligned before changing outreach copy or remote metadata:

- homepage: `https://yscjrh.github.io/skylattice/`
- what-is page: `https://yscjrh.github.io/skylattice/what-is-skylattice/`
- quick start: `https://yscjrh.github.io/skylattice/quickstart/`
- proof page: `https://yscjrh.github.io/skylattice/proof/`
- stable release page: `https://yscjrh.github.io/skylattice/releases/v0-2-2/`

## Weekly Four-Agent Review Loop

Run the discoverability review with four isolated perspectives so the same search context does not judge itself.

- Agent A: English discovery review for non-brand queries and official-source citations
- Agent B: Chinese discovery review for `/zh/` visibility, readability, and snippet quality
- Agent C: technical indexing review for Pages, `robots.txt`, `sitemap.xml`, `llms.txt`, JSON-LD, release status, homepage, and social preview
- Agent D: external authority scout for directories, comparison posts, and community surfaces that could truthfully mention Skylattice

Store raw local evidence under `.local/discoverability/`. Store public-safe summaries under `evals/ai-search/`.

## Cadence

- Day 0 baseline
- Day 7 follow-up
- Day 14 follow-up
- Day 30 follow-up
- weekly after Day 30

## Remote Settings

- keep GitHub `homepageUrl` set to `https://yscjrh.github.io/skylattice/`
- upload `docs/assets/social-preview.png` as the repository social preview image with the local automation:

```bash
python -m pip install -e .[automation]
python -m playwright install chromium
python tools/upload_github_social_preview.py --repository YSCJRH/skylattice
```

- keep the repository description aligned with `README.md`, `pyproject.toml`, and the Pages homepage
- keep topics aligned with the current positioning surface
- keep the latest GitHub release non-pre-release unless there is a deliberate preview posture again

## Pages Deployment

- keep the Pages workflow green on `main`
- set `NO_MKDOCS_2_WARNING=true` for local strict builds while the current Material release emits a policy warning unrelated to site correctness
- confirm the deployed site serves `robots.txt`, `sitemap.xml`, `llms.txt`, and `llms-full.txt`
- manually open the English root page and the Chinese mirror after each structural update

## Search Console And Bing

- verify the Pages site in Google Search Console
- verify the Pages site in Bing Webmaster Tools
- submit `https://yscjrh.github.io/skylattice/sitemap.xml`
- re-submit the sitemap after major public-page additions or slug changes

## Minimal External Authority Program

Keep these assets ready and keep their backlinks aimed at the canonical Pages surfaces:

- one stable non-pre-release release page
- one English launch post
- one Chinese launch post
- one category / comparison post
- one directory and community target tracker
- two to four short community-post drafts for different audiences
- one posting runbook and one set of reusable directory blurbs

Execution files live under `docs/outreach/`. Use `authority-program.md` as the 30-day sequence, `posting-runbook.md` as the posting checklist, and `directory-blurbs.md` for reusable short descriptions.

## Stable Release Follow-Up

- keep `v0.2.2` as the canonical stable release page and GitHub release target
- keep `v0.2.0` only as historical preview context
- keep `v0.2.1` as the first stable baseline in the public release history
- keep the Pages release page synced with the tracked GitHub release notes source
- refresh the weekly discoverability summary after any meaningful release, landing-page, or metadata change
- use `evals/ai-search/2026-04-10-post-release-review.md` as the first post-release checkpoint before the Day 14 review

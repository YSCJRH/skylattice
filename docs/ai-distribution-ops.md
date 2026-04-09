---
title: AI Distribution Ops
description: Operational checklist for keeping the Skylattice GitHub Pages site, repository metadata, and AI-search distribution surfaces aligned.
robots: noindex, follow
---

# AI Distribution Ops

Use this checklist whenever the public positioning, site structure, or release posture changes.

## Remote Settings

- set GitHub `homepageUrl` to `https://yscjrh.github.io/skylattice/`
- upload `docs/assets/social-preview.png` as the repository social preview image
- keep the repository description aligned with `README.md`, `pyproject.toml`, and the Pages homepage
- keep topics aligned with the current positioning surface

## Pages Deployment

- keep the Pages workflow green on `main`\r\n- set `NO_MKDOCS_2_WARNING=true` for local strict builds while the current Material release emits a policy warning unrelated to site correctness
- confirm the deployed site serves `robots.txt`, `sitemap.xml`, `llms.txt`, and `llms-full.txt`
- manually open the English root page and one Chinese mirror after each structural update

## Search Console And Bing

- verify the Pages site in Google Search Console
- verify the Pages site in Bing Webmaster Tools
- submit `https://yscjrh.github.io/skylattice/sitemap.xml`
- re-submit the sitemap after major public-page additions or slug changes

## AI-Search Benchmarking

- record Day 0 results immediately after launch
- re-run the benchmark at Day 14 and Day 30
- track whether AI tools cite the Pages site, GitHub README, or no official source at all
- capture recommendation quality, not only appearance rate

## Release Follow-Up

- keep `v0.2.0` as pre-release
- plan the next non-pre-release tag so GitHub can expose a non-null latest release signal
- keep the canonical Pages release page synced with the tracked GitHub release notes source

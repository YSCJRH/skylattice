---
title: AI Search Benchmark
description: Query clusters, scoring rules, and isolated-agent review steps for measuring whether Skylattice is becoming easier to discover and cite.
robots: noindex, follow
---

# AI Search Benchmark

Skylattice should be evaluated through isolated web-search reviews, not through one long conversational thread that contaminates later judgments.

## Review Model

Use four isolated agents or sessions for each review window:

- Agent A: English discovery
- Agent B: Chinese discovery
- Agent C: technical indexing and citation surface review
- Agent D: external authority scout

## What To Record

- whether Skylattice appears at all for non-brand queries
- whether the first official citation is the Pages site, the GitHub repo, or no official source
- whether the recommendation is accurate
- whether the answer confuses Skylattice with a generic coding agent, chat wrapper, or hosted bot
- whether Chinese snippets are readable and query-aligned
- whether external mentions and directory references have increased

## English Query Cluster

1. open-source local-first AI agent runtime
2. persistent memory agent with auditability
3. governed repo tasks open source
4. Git-native AI agent project
5. auditable agent framework with rollback
6. AI agent runtime you can verify without API keys

## Chinese Query Cluster

1. ???? AI Agent ??? ??
2. ?????? AI agent ??
3. ???? repo task ????
4. Git ?? AI agent ??
5. ??? AI agent ??
6. ????? ? AI agent ??

## Suggested Scorecard

| Review window | Agent | Query | Appeared? | First official source | Positioning accurate? | Snippet readable? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Day 0 | A | 1 |  |  |  |  |  |
| Day 0 | B | 1 |  |  |  |  |  |
| Day 0 | C | n/a |  |  |  |  |  |
| Day 0 | D | n/a |  |  |  |  |  |

Reuse the same table shape for Day 7, Day 14, Day 30, and the weekly follow-ups after Day 30.

## Output Locations

- raw notes, screenshots, and search transcripts stay local under `.local/discoverability/`
- public-safe summaries belong under `evals/ai-search/`

## Current Baseline

The current tracked baseline lives in `evals/ai-search/2026-04-09-baseline.md` and should be used as the reference point for the Day 7, Day 14, and Day 30 reviews.

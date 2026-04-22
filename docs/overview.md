# What Skylattice Is

For the canonical search-friendly overview page, start with [what-is-skylattice.md](what-is-skylattice.md). For the current stable release signal, start with [releases/v0-4-0.md](releases/v0-4-0.md).

Skylattice is a local-first AI agent runtime for people who want an agent they can inspect like software.

Most agent projects optimize for breadth, speed, or workflow convenience. Skylattice starts from a different question:

> What if a personal agent had to keep durable memory, act through explicit governance, and evolve through reviewable Git changes instead of hidden behavior drift?

That question shapes the whole repository.

## The Core Idea

Skylattice splits agent state into two surfaces on purpose:

- private runtime state lives under `.local/`
- durable system behavior lives in tracked files such as docs, configs, prompts, ADRs, and tests

This makes the runtime easier to reason about:

- memory can be persistent without becoming public by accident
- behavior changes can be reviewed like code
- automation can be bounded by policy instead of implied by prompts
- self-improvement can be rollbackable instead of mystical

## What It Already Demonstrates

Today the repository shows two concrete workflows.

### 1. Task Agent

A governed task path that can:

- plan bounded repo work
- materialize deterministic text edits
- validate changes with tracked commands
- record ledger events and memory writes
- prepare a draft PR when external writes are allowed

### 2. Technology Radar

A bounded discovery path that can:

- scan GitHub repositories through tracked topics and scoring rules
- record evidence and candidate scores
- run limited experiments on whitelisted paths
- promote tracked changes through a rollbackable Git path

## Why The Design Matters

Skylattice is useful even if you never run it in production, because it is a compact reference for several hard problems:

- how to separate private agent memory from public repository state
- how to make agent actions auditable after the fact
- how to keep CI and runtime validation aligned
- how to bound self-modification without pretending it does not exist

## Who It Is For

Skylattice is a strong fit for:

- builders exploring local-first agent infrastructure
- contributors interested in governance-heavy automation
- people who want a reference repo for memory, ledger, and Git-backed review boundaries

It is not yet a strong fit for:

- users expecting a hosted product
- teams wanting broad integrations out of the box
- workflows that need unrestricted tool use or autonomous production operations

## Where To Go Next

- start with [index.md](index.md) for the canonical landing page and [quickstart.md](quickstart.md) for the proof-first walkthrough
- read [use-cases.md](use-cases.md) for concrete user-facing scenarios
- read [comparison.md](comparison.md) to understand what Skylattice is and is not competing with
- read [architecture.md](architecture.md) if you want the runtime map
- open a GitHub issue with early feedback on the public repository

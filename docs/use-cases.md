# Use Cases

Skylattice is most useful for people who care about agent systems as infrastructure, not just as prompts.

## 1. Keep A Personal Agent Local, Durable, And Reviewable

Choose Skylattice when you want a personal agent runtime that:

- keeps real runtime memory under `.local/` instead of tracked Git history
- stores durable system behavior in legible docs, prompts, configs, and ADRs
- exposes health, run, memory, and radar inspection surfaces you can read without mutating state

Why it matters:

- you can grow a long-lived agent without turning the repo into a pile of opaque hidden state
- you can inspect what the system believes about itself before giving it more autonomy

## 2. Run Governed Repo Tasks Instead Of Unbounded Automation

Choose Skylattice when you want repo work that stays bounded:

- the planner declares file operations and validation commands up front
- repo and external writes still pass through approval gates
- task edits are deterministic and text-native, not arbitrary shell automation
- run inspection shows ledger events, materialized edit payloads, and memory writes after execution

Why it matters:

- you can understand what happened after a run, not just whether it passed
- you can use the project as a reference for reviewable AI-assisted repo operations

## 3. Learn From Open Source Without Turning The Runtime Into A Black Box

Choose Skylattice when you want a radar workflow that:

- discovers GitHub projects through tracked topics and scoring rules
- records evidence, experiments, promotions, and rollback metadata in a local ledger
- limits automatic promotion to whitelisted tracked paths
- keeps adoption state in `configs/radar/adoptions.yaml` instead of hidden model behavior

Why it matters:

- you can experiment with bounded self-improvement without giving the runtime silent write access everywhere
- you can inspect what the system learned, why it promoted something, and how to roll it back

## Who Should Care Today

- builders exploring local-first agent infrastructure
- contributors who want a small, inspectable reference repo for governance-heavy automation
- people comparing durable memory patterns, repo-task execution models, and Git-native rollback strategies

## Who Should Wait

Skylattice is still early if you need:

- a polished hosted product
- zero-config autonomous execution
- AST-aware refactors or arbitrary shell workflows
- a framework that optimizes for breadth over explicit operational boundaries

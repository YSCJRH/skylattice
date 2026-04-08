# Evolution Loop

## Goal

Skylattice should improve itself without becoming an unbounded autonomous system. Evolution is therefore artifact-driven, reviewable, and reversible.

## Allowed Evolution Targets

- memory abstractions and summaries
- strategy notes
- skill definitions
- tool routing preferences
- reusable task playbooks
- prompt and policy changes with controls

## Loop

1. **Observe**: collect signals from task outcomes, failures, operator feedback, and eval runs.
2. **Reflect**: generate candidate explanations for what should improve.
3. **Propose**: encode the change as a concrete candidate artifact or local state delta.
4. **Sandbox**: test the candidate in isolated runs, shadow mode, or redacted eval scenarios.
5. **Evaluate**: compare against explicit acceptance criteria, budgets, and safety checks.
6. **Promote or rollback**: merge the candidate into tracked or local durable state only if the evidence is sufficient.

## Promotion Gates

A change is promotable only when it is:

- logged in the ledger
- versioned in Git or local snapshots
- reviewable by a human operator
- reversible without manual archaeology
- linked to evidence or eval output

## Rollback Rules

- tracked artifacts roll back through Git history
- local runtime changes roll back through `.local/state/` or `.local/memory/` snapshots
- failed experiments remain visible in the ledger even when reverted

## What v0.1 Does Not Do

- no free-form prompt rewriting in production flows
- no automatic widening of permissions
- no unsupervised adaptation of user profile facts
- no hidden model fine-tuning

## Early Evaluation Signals

- fewer repeated user corrections
- better task decomposition quality
- fewer unnecessary approvals
- more reuse of approved playbooks
- stable or reduced cost for the same outcome quality

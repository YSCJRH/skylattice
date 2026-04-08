# Governance

## Purpose

Governance defines the maximum autonomy of the system. It exists to keep the agent helpful, proactive, and bounded.

In the current MVP, governance is enforced per run and per step, not only as a static policy document.

## Permission Tiers

| Tier | Meaning | Default in current MVP |
| --- | --- | --- |
| `observe` | read-only inspection, retrieval, summarization | auto-allowed |
| `local-safe-write` | reversible local writes in approved `.local/` paths | auto-allowed |
| `repo-write` | changes to tracked repository artifacts | explicit approval required |
| `external-write` | git push, GitHub writes, browser form submissions, external APIs | explicit approval required |
| `self-modify` | prompt, policy, skill, or routing updates affecting future behavior | explicit approval required |

## Run-Scoped Approval Model

Approvals are attached to a specific task run.

Current CLI behavior:

- `skylattice task run --allow repo-write`
- `skylattice task run --allow external-write`
- `skylattice task resume <run-id> --allow ...`

Important rules:

- approvals do not silently carry over to other runs
- approvals only unlock the explicit tier granted
- missing approval pauses the run at the first blocked step with status `waiting_approval`
- the ledger records both the pause and the later approval update

## Approval Rules

- destructive intent blocks automatic approval even inside `local-safe-write`
- repo writes need human review because they alter the durable tracked ledger
- external writes need human review because they create outside effects
- self-modification needs human review because it changes future behavior

## Budgets

Skylattice tracks budgets as policy artifacts rather than hidden runtime constants.

Current v0.1 budget categories:

- model token budget
- retry budget per plan
- wall-clock budget per background job
- external action budget

## Runtime Enforcement

The current runtime checks governance before each step.

Typical effects:

- file edits and commits require `repo-write`
- git push and GitHub sync require `external-write`
- read-only validation commands remain in `observe`

A blocked run is not discarded. It is resumable.

## Memory Editing Rules

- profile edits require provenance and should prefer superseding over overwriting
- episodic records are append-first and should preserve raw event order
- semantic compaction requires source links
- procedural edits require either tracked Git history or local snapshot history
- working memory is expected to be tombstoned or summarized at run end

## Self-Modification Restrictions

- no direct writes to tracked prompts or policies without a candidate, evidence, and approval
- no widening of allowed permission tiers from runtime code alone
- no silent changes to adapter routing precedence

## Destructive Guards

The system should escalate rather than proceed when it detects operations such as:

- delete or overwrite of durable records
- Git resets or history rewrites
- unreviewed memory compaction with data loss risk
- high-cost repeated retries without new evidence

## Freeze Mode

Freeze mode is an emergency brake.

When enabled:

- only `observe` actions are allowed by default
- pending maintenance or evolution work must stop
- manual operator review is required before resuming mutable actions

## Operator Posture

The system may be proactive in surfacing recurring needs or proposing plans, but it must not become self-authorizing.

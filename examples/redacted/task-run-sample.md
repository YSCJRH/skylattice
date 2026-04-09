# Task Run Sample

This walkthrough shows what a successful, public-safe task run looks like when Skylattice executes a governed repo task through deterministic edit modes.

## Scenario

Goal:

> Refresh the README with deterministic edit primitives.

Setup:

- provider: repository fake provider
- GitHub writes: fake adapter returning a draft PR URL
- validation command: `git diff --stat`
- approvals: repo write and external write both granted

## What Happens

1. Skylattice creates a `codex/...` working branch.
2. The planner chooses three deterministic text edits for `README.md`:
   - `replace_text`
   - `insert_after`
   - `append_text`
3. The runtime materializes each edit payload and records it in step results and ledger events.
4. The repo runs the tracked validation command.
5. The run commits, pushes, and prepares a draft PR.
6. The runtime tombstones working memory and records episodic plus procedural memory for the completed run.

## What To Look For In The JSON

Open [task-run-sample.json](task-run-sample.json) and check for these signals:

- `run.status` is `completed`
- step actions include `workspace.replace_text`, `workspace.insert_after`, and `workspace.append_text`
- each edit step includes a `materialized_edit` payload and `verification_metadata`
- the final run result includes a draft PR URL
- memory shows a tombstoned working record plus active episodic and procedural records

## Why This Matters

The sample demonstrates the core claim of the repository: Skylattice is not just a prompt shell. It records the exact edit payloads it executes, validates them through tracked commands, and leaves behind an inspectable memory and ledger trail.

# Redacted Examples

This directory contains public-safe example outputs and walkthroughs for people who want to verify that Skylattice is real before they add credentials.

## Included Samples

- `doctor-output.json`: a representative zero-credential `skylattice doctor` result
- `task-run-sample.md`: a guided walkthrough of a successful governed task run
- `task-run-sample.json`: a sanitized `task inspect` payload with materialized edits and memory writes
- `radar-sample.md`: a guided walkthrough of a successful radar run
- `radar-run-sample.json`: a sanitized `radar inspect` payload with candidates, evidence, promotions, and memory

## Source Of Truth

- the doctor sample is based on the real local `python -m skylattice.cli doctor` output with stable, public-safe values
- the task and radar samples are generated from repository test doubles so they stay reproducible and do not require private credentials or real GitHub writes
- IDs and timestamps are normalized where helpful to keep the examples stable and easy to read

## Safe To Commit

Acceptable examples:

- sample command output
- redacted run inspection payloads
- example task briefs
- redacted eval reports
- schema-level examples without private user data

Do not place private memory, secrets, raw logs, absolute local filesystem paths, or exported `.local/` artifacts here.

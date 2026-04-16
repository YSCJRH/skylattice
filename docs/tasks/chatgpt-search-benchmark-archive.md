# Task Brief: ChatGPT Search Benchmark Archive

## Intent

- Archive the old `codex/chatgpt-search-benchmark` branch before deleting it locally, so the repo keeps a durable explanation of what the branch was, why it was not merged directly, and how to revisit the idea later.
- Success means the branch can be removed without losing context, and future maintainers can tell the difference between "unfinished work" and "completed experimental checkpoint on an older product direction."

## Constraints

- tracked artifacts to edit: `docs/tasks/chatgpt-search-benchmark-archive.md`
- local-only artifacts expected to change: local git tag metadata
- explicit non-goals: no resurrection of the benchmark harness, no merge into `main`, no new benchmark implementation work in this task

## Affected Subsystems

- branch hygiene and local repository maintenance
- archived product/context notes for AI-search experimentation

## Verification

- `git diff --check`
- confirm local archive tag exists for commit `f7a8c0bd7ac5d760f877cbd21022daac0b8a159f`
- confirm local branch `codex/chatgpt-search-benchmark` can be deleted after this note is committed

## Notes

### Archived Branch

- branch: `codex/chatgpt-search-benchmark`
- tip commit: `f7a8c0bd7ac5d760f877cbd21022daac0b8a159f`
- local archive tag: `archive/chatgpt-search-benchmark-2026-04-17`
- tip summary: `eval: checkpoint private chatgpt search benchmark`

### What The Branch Was For

The branch implemented an automated **ChatGPT Search benchmark harness** with:

- tracked prompt and agent registries under `configs/public/`
- a `src/skylattice/benchmarks/` module for orchestration, scoring, reporting, and Playwright execution
- CLI wiring for `benchmark chatgpt-search run|summary|report`
- dedicated benchmark tests under `tests/test_chatgpt_search_benchmark.py`

### Completion Judgment

This branch was **not** a half-built spike in the narrow engineering sense:

- its benchmark-specific tests passed
- its code compiled
- the CLI surface was wired when run from the branch source tree

However, it also did **not** complete the work required to land on the current `main` line:

- it was never proposed through a GitHub PR
- it was built against an older `v0.2.x` product state
- its automated ChatGPT Search harness direction diverged from the later `main` line, which now uses a more conservative isolated-review workflow documented in `docs/ai-search-benchmark.md`

### Why It Was Not Merged Directly

The branch is best treated as a finished experimental checkpoint on an older direction, not as a clean missing patch for current `main`.

Direct merge was rejected because it would introduce a large, unreviewed benchmark subsystem whose product assumptions no longer match the current public evaluation posture.

### If We Revisit This Later

Do **not** revive this work by merging the archived commit range directly.

Preferred path:

1. start from current `main`
2. write a fresh task brief that explains why automated ChatGPT Search benchmarking is worth reviving now
3. import only the pieces that still fit the current product and governance posture

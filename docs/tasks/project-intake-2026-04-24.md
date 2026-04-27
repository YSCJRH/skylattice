# Task Brief: Project Intake 2026-04-24

## Intent

- Capture the current Skylattice project intake after reviewing the tracked rules, public docs, architecture docs, task history, configs, and selected runtime entrypoints.
- Success means the next product-shape discussion can start from current repository evidence instead of reconstructing context from chat history.
- Keep this as a handoff and decision-prep artifact, not an implementation plan that silently changes product direction.

## Constraints

- tracked artifacts to edit: `docs/tasks/project-intake-2026-04-24.md`
- local-only artifacts expected to change: none
- explicit non-goals: no code changes, no stable-page rewrite, no governance widening, no Hosted Alpha repositioning, no validation run that mutates `.local/`

## Affected Subsystems

- docs and public positioning: current first-run paths, public proof surface, product-preview story, and stable release posture
- architecture and runtime: local-first execution boundary, task-agent composition root, web bridge, and radar delegation
- governance and memory: approval tiers, private local memory, review-driven memory operations, and non-runtime hosted summaries
- radar and evolution: provider abstraction, schedule intent, promotion allowlist, adoption registry, and rollbackable behavior change
- hosted web control plane: preview, Hosted Alpha deployment contract, pairing, connector, command queue, and local executor boundary

## Verification

- read project rules and intake method: `AGENTS.md`, the local `parallel-project-intake` Codex skill
- confirmed requested knowledge-entry gaps: root `action.md` and `wiki/index.md` are not present in this repository
- read core docs: `README.md`, `docs/architecture.md`, `docs/governance.md`, `docs/memory-model.md`, `docs/technology-radar.md`, `docs/web-control-plane.md`, `docs/github-workflow.md`
- read current state docs: `docs/roadmap.md`, `docs/releases/v0-4-1.md`, `docs/tasks/project-handover-baseline.md`, `docs/tasks/mainline-refresh-2026-04-17.md`, `docs/tasks/phase-5-operational-closure-status.md`
- read cold-start pages: `docs/quickstart.md`, `docs/proof.md`, `docs/app-preview.md`
- read selected code/config entrypoints: `pyproject.toml`, `package.json`, `apps/web/README.md`, `apps/web/package.json`, `configs/policies/governance.yaml`, `configs/task/validation.yaml`, `configs/radar/*.yaml`, `src/skylattice/cli.py`, `src/skylattice/runtime/service.py`, `src/skylattice/runtime/db.py`, `src/skylattice/api/app.py`, `src/skylattice/web/connector.py`
- read-only repository checks: `git status --short --branch`, `git remote -v`, `git log --oneline --decorate --max-count=8`, `git ls-files .local`
- not run in this intake: `python -m skylattice.cli doctor`, `python -m pytest`, `python -m compileall`, `npm run web:preview:check`, or `mkdocs build`

## Notes

### Intake Classification

- task type: `mixed`
- primary mode: `research-evidence` plus `knowledge-maintenance`
- not treated as: `code-change`
- default mode used: read-first; implementation was limited to this tracked task brief after the operator asked to complete the immediate follow-up

### Current Project Judgment

- Skylattice is best understood as a local-first, governance-heavy, auditable agent runtime and reference implementation.
- The local runtime remains the execution authority; GitHub is an audit, collaboration, discovery, and distribution surface; the hosted web app is a control plane, not runtime truth.
- `v0.4.1` is the current stable public release surface, with the latest release story focused on Hosted Alpha deployment semantics and clearer preview/live boundaries.
- Phases 0 through 4 are complete; Phase 5 remains the current operational-closure track around radar scheduling, provider abstraction, prompt truth-source alignment, and honest auth-dependent validation.

### Cold-Start Path Review

- `docs/quickstart.md` names `install -> doctor -> pytest -> validation suite` as the fastest no-credential success path.
- `docs/quickstart.md` also presents `npm run web:preview` as the fastest product-shaped preview path, not as runtime verification.
- `docs/proof.md` aligns with that split: no-credential verification is the fastest proof, while web preview is product proof.
- `docs/app-preview.md` keeps the preview boundary explicit: it is read-only, seeded, not a hosted runtime, not a live account, and not connected to a real local agent by default.
- Current judgment: the cold-start pages are directionally consistent enough to support the next product-shape discussion without immediate stable-page edits.

### Structure Map

- product and proof surface: `README.md`, `docs/index.md`, `docs/quickstart.md`, `docs/proof.md`, `docs/releases/`, `examples/redacted/`
- local runtime surface: `src/skylattice/runtime/service.py`, `src/skylattice/cli.py`, `src/skylattice/runtime/db.py`, `src/skylattice/planning/`, `src/skylattice/actions/`, `src/skylattice/providers/`
- governance and memory surface: `docs/governance.md`, `docs/memory-model.md`, `configs/policies/governance.yaml`, `src/skylattice/memory/`, `src/skylattice/governance/`
- radar and evolution surface: `docs/technology-radar.md`, `configs/radar/*.yaml`, `src/skylattice/radar/`, `docs/adrs/0012-*` through `docs/adrs/0017-*`
- web control-plane surface: `apps/web/`, `docs/web-control-plane.md`, `docs/ops/hosted-alpha-runbook.md`, `src/skylattice/api/bridge.py`, `src/skylattice/web/connector.py`, `docs/adrs/0018-hosted-web-control-plane-and-local-bridge.md`

### Confirmed Boundaries

- `.local/**` is private runtime state and must not be committed.
- The system is intentionally single-process and local-first unless a future ADR says otherwise.
- Hosted app commands resolve back to local governance tiers and do not bypass approvals.
- FastAPI public memory routes remain read-only; memory review and write workflows are CLI-first.
- Radar writes are bounded by tracked config, promotion gates, path allowlists, ledger records, and Git rollback metadata.
- Automatic promotion is constrained to whitelisted tracked paths and must not silently widen into general self-modification.

### Risks And Unknowns

- `TaskAgentService` is the main orchestration center and remains a high-change-risk hotspot.
- SQLite schema evolution is startup-driven through table/column creation rather than a versioned migration system.
- Radar promotion can touch high-leverage roots such as `prompts`, `skills`, `src/skylattice/actions`, and `src/skylattice/providers`; this is bounded but still deserves careful review before widening.
- Hosted app summary mirrors are intentionally lightweight, but the exact minimization/redaction boundary for mirrored runtime summaries is not yet as concrete as the runtime/local-state boundary.
- Memory exports are documented under `.local/memory/exports`, while tracked governance local-safe roots list `.local/work`, `.local/logs`, and `.local/state`; this may be fine through a memory-specific path, but it is a doc/config alignment point worth checking before changing memory behavior.
- GitLab is enabled as a second live provider, while tracked schedules remain GitHub-oriented; this appears intentional but should be stated explicitly if product shape work touches radar.

### Recommended Next Decision Frame

Before choosing the next product shape, decide which of these should be the primary next wedge:

- Phase 5 closeout: repeatable safe weekly validation and honest credential-dependent reporting.
- Hosted Alpha onboarding: make preview, live pairing, blocked mode, and local executor boundaries easy for cold users to understand.
- Runtime architecture cleanup: reduce risk around `TaskAgentService`, serializer leakage, schema evolution, or connector backpressure before adding product surface.

Do not decide by broad preference alone. Tie the choice to one or two observable acceptance criteria, such as a repeatable validation record, a successful Hosted Alpha first-run checklist, or a narrowed runtime hotspot with tests.

### Immediate Follow-Up Options

1. Review this brief and choose the next product-shape wedge.
2. If the wedge is Hosted Alpha onboarding, audit `docs/quickstart.md`, `docs/app-preview.md`, `docs/web-control-plane.md`, and `docs/ops/hosted-alpha-runbook.md` as one user journey.
3. If the wedge is Phase 5 closeout, turn `docs/tasks/phase-5-operational-closure-status.md` into a concrete closeout checklist and run the minimal validation set in an environment where `.local/` changes are expected.

# Radar Weekly Validation Record

## Validation Window

- Date: 2026-04-17
- Validation mode: `safe-validation`
- Trigger method: manual CLI trigger via `python -m skylattice.cli radar schedule run --schedule weekly-github`
- Runtime environment: disposable sibling validation clone on a clean `main` checkout
- Promotion capability during pass: disabled by a clone-local `promotion_limit: 0` override
- Credential prerequisites: GitHub token access plus an explicit `SKYLATTICE_GITHUB_REPOSITORY` hint inside the validation shell
- Credential availability during pass: explicit bridge used in the disposable validation shell via `gh auth token` plus `SKYLATTICE_GITHUB_REPOSITORY=YSCJRH/skylattice`
- Schedule ID: `weekly-github`
- Run ID: `radar-52677865a3c74541a91f61c30a70feb9`
- Validation report path: `.local/radar/validations/20260417T091226Z-radar-52677865a3c74541a91f61c30a70feb9.json` in the disposable sibling validation clone

## Expected Alignment

- `trigger_mode` matched tracked schedule intent: yes
- `schedule_id` matched tracked schedule intent: yes
- `window` matched tracked schedule intent: yes
- `limit` matched tracked schedule intent: yes
- run completed successfully: yes

## Observed Outcome

- Overall validation result: `valid`
- Validation report generated: `yes`
- Promotions created: `0`
- Any freeze or failure signals: none observed
- Manual intervention points: explicit credential bridging from `gh`, a committed clone-local `promotion_limit: 0` override, and manual carry-forward of the local report summary into this tracked note

## Operator Notes

- Task registration still points at the repository root: not exercised through Windows Task Scheduler in this record; `radar schedule render` in the disposable sibling clone pointed at the clone root as expected
- Safe no-promotion override used: yes; the disposable sibling clone committed a local `promotion_limit: 0` override before the run so the normal direct-to-`main` promotion path could not fire
- Any local environment drift noticed: no runtime drift after explicit bridge; the validation clone started from a clean `main` worktree, recorded `trigger_mode=scheduled` and `schedule_id=weekly-github`, and produced a valid local report
- Follow-up action needed: optional next step is a separate live-promotion-capable operator pass; keep that distinct from the weekly safe-validation path

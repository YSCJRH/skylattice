# Radar Weekly Validation Record

## Validation Window

- Date: 2026-04-16
- Validation mode: `safe-validation`
- Credential availability: `GITHUB_TOKEN` present in the isolated validation clone environment
- Schedule ID: `weekly-github`
- Run ID: `radar-9ad74e9075cb4791879c0efbfa4e2181`
- Validation report path: `.local/radar/validations/20260416T070345Z-radar-9ad74e9075cb4791879c0efbfa4e2181.json` in the isolated validation clone

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

## Operator Notes

- Task registration still points at the repository root: not exercised through Windows Task Scheduler in this record; `radar schedule render` targeted the isolated validation clone root as expected
- Safe no-promotion override used: yes; the isolated validation clone used a local no-promotion threshold override so the weekly pass could exercise the schedule path without live promotion side effects
- Any local environment drift noticed: yes; at the time of the first run, a validation clone rooted under `.local/work/` was not suitable for live radar experimentation because `RepoWorkspaceAdapter` protected repositories whose root path contained `.local`, which blocked writes to `docs/radar/experiments/`
- Follow-up action needed: completed after this record; `RepoWorkspaceAdapter` now checks protected path parts relative to the repo root, and a post-fix rerun from `.local/work/` (`radar-3ff238e283e9447cb6af7b4cbac2035c`) advanced to the experiment branch instead of failing with `Path is protected`
- Additional safety note: this isolated run used a local no-promotion threshold override to avoid remote side effects, so promotion push behavior was intentionally not exercised in this record

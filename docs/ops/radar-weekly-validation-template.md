# Radar Weekly Validation Record

Use this template after running:

```bash
python -m skylattice.cli radar schedule validate --schedule weekly-github
```

This template is tracked on purpose, but Skylattice does not write into it automatically. Fill it from the local validation report under `.local/radar/validations/` only when you want a reviewable weekly record in the repository.

## Validation Window

- Date:
- Validation mode:
- Credential availability:
- Schedule ID:
- Run ID:
- Validation report path:

## Expected Alignment

- `trigger_mode` matched tracked schedule intent:
- `schedule_id` matched tracked schedule intent:
- `window` matched tracked schedule intent:
- `limit` matched tracked schedule intent:
- run completed successfully:

## Observed Outcome

- Overall validation result:
- Validation report generated:
- Promotions created:
- Any freeze or failure signals:

## Operator Notes

- Task registration still points at the repository root:
- Safe no-promotion override used:
- Any local environment drift noticed:
- Follow-up action needed:

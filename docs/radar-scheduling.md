# Radar Scheduling

Skylattice treats radar scheduling as tracked operator intent, not as a hidden background worker.

The schedule itself lives in `configs/radar/schedule.yaml`, while the operating system remains responsible for recurring execution.

## What This Covers

- inspect tracked radar schedules
- render Windows Task Scheduler registration details
- run a tracked schedule immediately without waiting for the next trigger
- validate that a weekly schedule keeps using the normal bounded `radar scan` path

## Inspect The Tracked Schedule

Use the CLI to see the default schedule and every declared entry:

```bash
python -m skylattice.cli radar schedule show
```

This tells you:

- which schedule is the default
- whether each schedule is enabled
- which `window` and `limit` it resolves to
- which tracked `target_command` it will run
- which Windows task metadata is associated with it

## Render Windows Task Registration Details

Use the tracked render surface before you register anything:

```bash
python -m skylattice.cli radar schedule render --target windows-task
```

The rendered payload is the operator truth for Windows registration. It now includes:

- the absolute repository working directory
- the exact PowerShell action Skylattice expects the task to run
- the decoded action script, plus the encoded PowerShell command used for safe Task Scheduler registration
- the tracked trigger command, when the schedule is meant to run automatically
- helper commands to inspect, trigger, and unregister the task

The default weekly schedule renders a task that:

- starts from the repository root
- runs `python -m skylattice.cli radar schedule run --schedule weekly-github`
- uses the tracked weekly trigger command from `configs/radar/schedule.yaml`

## Register The Windows Task

Recommended flow:

1. render the schedule
2. review the `register_command`
3. paste that command into an elevated PowerShell window only after confirming the trigger still matches your intent

For the shipped weekly example, the tracked trigger command is:

```powershell
New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am
```

If your local weekly cadence should be different, edit the tracked config first, then re-render the registration details.

## Run A First Manual Check

Before waiting for the next scheduled time, trigger the task once yourself:

```bash
python -m skylattice.cli radar schedule run --schedule weekly-github
```

Or, after registration, use the rendered helper command:

```powershell
Start-ScheduledTask -TaskName "Skylattice Radar weekly-github" -TaskPath "\Skylattice"
```

Success means:

- the run completes through the normal radar workflow
- the resulting radar run uses the tracked `weekly` window and configured `limit`
- the inspected radar run records `trigger_mode=scheduled` and `schedule_id=weekly-github`
- no hidden scheduler state is introduced inside Skylattice

## Weekly-Cycle Validation Checklist

When validating a real scheduled weekly cycle, check:

- the task is still registered under the tracked folder and name
- the task starts in the repository root instead of `system32`
- the created radar run records the expected `weekly` window
- the created radar run records the expected `schedule_id` and `trigger_mode`
- any promotion or failure still flows through the normal ledger, memory, and rollback surfaces
- the repository remains clean before each scheduled run starts

## Why This Stays OS-Level

Skylattice intentionally avoids a resident scheduler, daemon, or internal job queue.

That keeps recurring execution:

- local-first
- reviewable through tracked config
- explicit about operator responsibility
- separate from GitHub, which remains an audit and collaboration layer instead of runtime truth

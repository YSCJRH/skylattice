"""Command-line entry points for Skylattice."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from skylattice.runtime import TaskAgentService


def build_doctor_report() -> dict[str, object]:
    """Return a compact local status report for the executable runtime."""
    return TaskAgentService.from_repo().doctor_report()


def _dump(payload: dict[str, object]) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skylattice")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("doctor", help="Show kernel, governance, and runtime summary.")

    task_parser = subparsers.add_parser("task", help="Run and inspect task-agent executions.")
    task_subparsers = task_parser.add_subparsers(dest="task_command")

    run_parser = task_subparsers.add_parser("run", help="Create and execute a new task run.")
    run_parser.add_argument("--goal", required=True, help="Inline goal text or a path to a goal file.")
    run_parser.add_argument("--allow", action="append", default=[], choices=["repo-write", "external-write"])

    status_parser = task_subparsers.add_parser("status", help="Show run status.")
    status_parser.add_argument("run_id")

    resume_parser = task_subparsers.add_parser("resume", help="Resume a paused task run.")
    resume_parser.add_argument("run_id")
    resume_parser.add_argument("--allow", action="append", default=[], choices=["repo-write", "external-write"])

    inspect_parser = task_subparsers.add_parser("inspect", help="Show full run details.")
    inspect_parser.add_argument("run_id")

    args = parser.parse_args(argv)
    service = TaskAgentService.from_repo()

    try:
        if args.command == "doctor":
            _dump(build_doctor_report())
            return 0

        if args.command == "task":
            allows = set(getattr(args, "allow", []) or [])
            if args.task_command == "run":
                run = service.run_task(
                    goal_input=args.goal,
                    allow_repo_write="repo-write" in allows,
                    allow_external_write="external-write" in allows,
                )
                _dump(service.inspect_run(run.run_id))
                return 0
            if args.task_command == "status":
                _dump(service._serialize_run(service.get_run(args.run_id)))
                return 0
            if args.task_command == "resume":
                run = service.resume_task(
                    run_id=args.run_id,
                    allow_repo_write="repo-write" in allows,
                    allow_external_write="external-write" in allows,
                )
                _dump(service.inspect_run(run.run_id))
                return 0
            if args.task_command == "inspect":
                _dump(service.inspect_run(args.run_id))
                return 0
        parser.print_help()
        return 0
    except KeyError as exc:
        _dump({"status": "error", "error": str(exc)})
        return 1
    except RuntimeError as exc:
        _dump({"status": "error", "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

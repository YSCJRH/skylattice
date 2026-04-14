"""Command-line entry points for Skylattice."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from skylattice.memory.interfaces import MemoryLayer, RecordStatus
from skylattice.runtime import TaskAgentService

MEMORY_LAYER_CHOICES = [layer.value for layer in MemoryLayer]
MEMORY_STATUS_CHOICES = [status.value for status in RecordStatus]


def build_doctor_report() -> dict[str, object]:
    """Return a compact local status report for the executable runtime."""
    return TaskAgentService.from_repo().doctor_report()


def _dump(payload: dict[str, object] | list[dict[str, object]]) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _coerce_layers(values: list[str] | None) -> tuple[MemoryLayer, ...] | None:
    if not values:
        return None
    return tuple(MemoryLayer(value) for value in values)


def _coerce_statuses(values: list[str] | None) -> tuple[RecordStatus, ...] | None:
    if not values:
        return None
    return tuple(RecordStatus(value) for value in values)


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

    radar_parser = subparsers.add_parser("radar", help="Run and inspect the technology radar workflow.")
    radar_subparsers = radar_parser.add_subparsers(dest="radar_command")

    scan_parser = radar_subparsers.add_parser("scan", help="Scan GitHub for new technical candidates.")
    scan_parser.add_argument("--window", choices=["weekly", "manual"], default="manual")
    scan_parser.add_argument("--limit", type=int)

    radar_status_parser = radar_subparsers.add_parser("status", help="Show radar run status.")
    radar_status_parser.add_argument("run_id")

    radar_inspect_parser = radar_subparsers.add_parser("inspect", help="Inspect a radar run or candidate.")
    radar_inspect_parser.add_argument("identifier")

    radar_replay_parser = radar_subparsers.add_parser("replay", help="Replay a candidate through the radar workflow.")
    radar_replay_parser.add_argument("candidate_id")

    radar_rollback_parser = radar_subparsers.add_parser("rollback", help="Roll back a radar promotion.")
    radar_rollback_parser.add_argument("promotion_id")

    memory_parser = subparsers.add_parser("memory", help="Review and search local memory.")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command")

    memory_list_parser = memory_subparsers.add_parser("list", help="List local memory records.")
    memory_list_parser.add_argument("--layer", action="append", choices=MEMORY_LAYER_CHOICES)
    memory_list_parser.add_argument("--status", action="append", choices=MEMORY_STATUS_CHOICES)
    memory_list_parser.add_argument("--limit", type=int, default=50)

    memory_inspect_parser = memory_subparsers.add_parser("inspect", help="Inspect a single memory record.")
    memory_inspect_parser.add_argument("record_id")

    memory_search_parser = memory_subparsers.add_parser("search", help="Search ranked local memory.")
    memory_search_parser.add_argument("--query", required=True)
    memory_search_parser.add_argument("--layer", action="append", choices=MEMORY_LAYER_CHOICES)
    memory_search_parser.add_argument("--status", action="append", choices=MEMORY_STATUS_CHOICES)
    memory_search_parser.add_argument("--limit", type=int, default=5)

    memory_profile_parser = memory_subparsers.add_parser("profile", help="Manage profile memory proposals.")
    profile_subparsers = memory_profile_parser.add_subparsers(dest="profile_command")
    profile_propose_parser = profile_subparsers.add_parser("propose", help="Propose a reviewed profile memory update.")
    profile_propose_parser.add_argument("--key", required=True)
    profile_propose_parser.add_argument("--value", required=True)
    profile_propose_parser.add_argument("--reason", required=True)

    memory_review_parser = memory_subparsers.add_parser("review", help="Inspect and resolve pending memory proposals.")
    review_subparsers = memory_review_parser.add_subparsers(dest="review_command")
    review_list_parser = review_subparsers.add_parser("list", help="List constrained memory proposals.")
    review_list_parser.add_argument("--limit", type=int, default=50)
    review_confirm_parser = review_subparsers.add_parser("confirm", help="Confirm a constrained memory proposal.")
    review_confirm_parser.add_argument("record_id")
    review_reject_parser = review_subparsers.add_parser("reject", help="Reject a constrained memory proposal.")
    review_reject_parser.add_argument("record_id")

    memory_semantic_parser = memory_subparsers.add_parser("semantic", help="Manage semantic memory compaction.")
    semantic_subparsers = memory_semantic_parser.add_subparsers(dest="semantic_command")
    semantic_compact_parser = semantic_subparsers.add_parser("compact", help="Create semantic compaction proposals.")
    semantic_compact_parser.add_argument("--create-proposals", action="store_true")

    memory_procedural_parser = memory_subparsers.add_parser("procedural", help="Manage procedural memory dedup proposals.")
    procedural_subparsers = memory_procedural_parser.add_subparsers(dest="procedural_command")
    procedural_dedup_parser = procedural_subparsers.add_parser("dedup", help="Create procedural dedup proposals.")
    procedural_dedup_parser.add_argument("--create-proposals", action="store_true")

    memory_rollback_parser = memory_subparsers.add_parser("rollback", help="Roll back an active memory record.")
    memory_rollback_parser.add_argument("record_id")

    memory_export_parser = memory_subparsers.add_parser("export", help="Export local memory records to .local.")
    memory_export_parser.add_argument("--layer", action="append", choices=MEMORY_LAYER_CHOICES)
    memory_export_parser.add_argument("--status", action="append", choices=MEMORY_STATUS_CHOICES)
    memory_export_parser.add_argument("--output")

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
                _dump(
                    {
                        "run": service._serialize_run(service.get_run(args.run_id)),
                        "recovery": service.get_run_recovery(args.run_id),
                    }
                )
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

        if args.command == "radar":
            if args.radar_command == "scan":
                run = service.scan_radar(window=args.window, limit=args.limit)
                _dump(service.inspect_radar_run(run.run_id))
                return 0
            if args.radar_command == "status":
                _dump(service.radar._serialize_run(service.get_radar_run(args.run_id)))
                return 0
            if args.radar_command == "inspect":
                _dump(service.inspect_radar_target(args.identifier))
                return 0
            if args.radar_command == "replay":
                run = service.replay_radar_candidate(args.candidate_id)
                _dump(service.inspect_radar_run(run.run_id))
                return 0
            if args.radar_command == "rollback":
                promotion = service.rollback_radar_promotion(args.promotion_id)
                _dump(service.radar._serialize_promotion(promotion))
                return 0

        if args.command == "memory":
            layers = _coerce_layers(getattr(args, "layer", None))
            statuses = _coerce_statuses(getattr(args, "status", None))
            if args.memory_command == "list":
                _dump(service.list_memory_records(layers=layers, statuses=statuses, limit=args.limit))
                return 0
            if args.memory_command == "inspect":
                _dump(service.inspect_memory_record(args.record_id))
                return 0
            if args.memory_command == "search":
                _dump(service.search_memory(query=args.query, layers=layers, statuses=statuses, limit=args.limit))
                return 0
            if args.memory_command == "profile" and args.profile_command == "propose":
                _dump(service.propose_profile_memory(key=args.key, value=args.value, reason=args.reason))
                return 0
            if args.memory_command == "review":
                if args.review_command == "list":
                    _dump(service.list_memory_review_queue(limit=args.limit))
                    return 0
                if args.review_command == "confirm":
                    _dump(service.confirm_memory_record(args.record_id))
                    return 0
                if args.review_command == "reject":
                    _dump(service.reject_memory_record(args.record_id))
                    return 0
            if args.memory_command == "semantic" and args.semantic_command == "compact":
                if not args.create_proposals:
                    raise RuntimeError("memory semantic compact requires --create-proposals")
                records = service.create_semantic_compaction_proposals()
                _dump({"count": len(records), "records": records})
                return 0
            if args.memory_command == "procedural" and args.procedural_command == "dedup":
                if not args.create_proposals:
                    raise RuntimeError("memory procedural dedup requires --create-proposals")
                records = service.create_procedural_dedup_proposals()
                _dump({"count": len(records), "records": records})
                return 0
            if args.memory_command == "rollback":
                _dump(service.rollback_memory_record(args.record_id))
                return 0
            if args.memory_command == "export":
                _dump(service.export_memory_records(layers=layers, statuses=statuses, output_path=args.output))
                return 0

        parser.print_help()
        return 0
    except (KeyError, RuntimeError, ValueError) as exc:
        _dump({"status": "error", "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

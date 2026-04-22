"""Authenticated bridge API for the hosted Skylattice web control plane."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from skylattice.memory.interfaces import MemoryLayer, RecordStatus
from skylattice.runtime import TaskAgentService
from skylattice.web import WebConnectorConfig

from .app import get_task_agent_service

router = APIRouter(prefix="/bridge/v1", tags=["web-bridge"])


class TaskRunRequest(BaseModel):
    goal: str = Field(min_length=1)
    allow_repo_write: bool = False
    allow_destructive_repo_write: bool = False
    allow_external_write: bool = False


class TaskResumeRequest(BaseModel):
    allow_repo_write: bool = False
    allow_destructive_repo_write: bool = False
    allow_external_write: bool = False


class RadarScanRequest(BaseModel):
    window: str = "manual"
    limit: int | None = None


class RadarScheduleRunRequest(BaseModel):
    schedule_id: str | None = None


class RadarScheduleValidateRequest(BaseModel):
    schedule_id: str | None = None
    run_id: str | None = None
    output_path: str | None = None


class RadarCandidateReplayRequest(BaseModel):
    candidate_id: str = Field(min_length=1)


class RadarPromotionRollbackRequest(BaseModel):
    promotion_id: str = Field(min_length=1)


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=1)
    layers: list[MemoryLayer] = Field(default_factory=list)
    statuses: list[RecordStatus] = Field(default_factory=list)
    limit: int = 5


class MemoryProfileProposalRequest(BaseModel):
    key: str = Field(min_length=1)
    value: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class MemoryReviewRequest(BaseModel):
    record_id: str = Field(min_length=1)


class CommandAckRequest(BaseModel):
    command_id: str = Field(min_length=1)
    accepted: bool = True


def require_bridge_key(
    authorization: Annotated[str | None, Header()] = None,
    x_skylattice_bridge_key: Annotated[str | None, Header()] = None,
) -> str:
    expected = str(os.environ.get("SKYLATTICE_WEB_BRIDGE_KEY", "")).strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SKYLATTICE_WEB_BRIDGE_KEY is not configured for the local bridge.",
        )
    provided = (x_skylattice_bridge_key or "").strip()
    if not provided and authorization:
        parts = authorization.strip().split(" ", maxsplit=1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            provided = parts[1].strip()
    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bridge authentication failed.",
        )
    return provided


@router.get("/status")
def bridge_status(
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    connector = WebConnectorConfig.from_repo(service.repo_root)
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
        "bridge": connector.bridge_auth_payload(),
        "connector": connector.status_payload(),
        "doctor": service.doctor_report(),
        "auth": service.auth_preflight_report(),
    }


@router.get("/doctor")
def bridge_doctor(
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.doctor_report()


@router.get("/auth-preflight")
def bridge_auth_preflight(
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.auth_preflight_report()


@router.get("/pairing/status")
def pairing_status(
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    connector = WebConnectorConfig.from_repo(service.repo_root)
    return {
        "status": "ok",
        "pairing": connector.status_payload(),
        "bridge": connector.bridge_auth_payload(),
    }


@router.post("/task/runs")
def create_task_run(
    request: TaskRunRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    run = service.run_task(
        goal_input=request.goal,
        allow_repo_write=request.allow_repo_write,
        allow_destructive_repo_write=request.allow_destructive_repo_write,
        allow_external_write=request.allow_external_write,
    )
    return service.inspect_run(run.run_id)


@router.post("/task/runs/{run_id}/resume")
def resume_task_run(
    run_id: str,
    request: TaskResumeRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    run = service.resume_task(
        run_id=run_id,
        allow_repo_write=request.allow_repo_write,
        allow_destructive_repo_write=request.allow_destructive_repo_write,
        allow_external_write=request.allow_external_write,
    )
    return service.inspect_run(run.run_id)


@router.get("/task/runs/{run_id}")
def inspect_task_run(
    run_id: str,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.inspect_run(run_id)


@router.get("/task/runs/{run_id}/events")
def inspect_task_run_events(
    run_id: str,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> list[dict[str, object]]:
    return service.inspect_run(run_id)["events"]


@router.get("/task/runs/{run_id}/memory")
def inspect_task_run_memory(
    run_id: str,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> list[dict[str, object]]:
    return service.inspect_run(run_id)["memory"]


@router.get("/task/runs/{run_id}/recovery")
def inspect_task_run_recovery(
    run_id: str,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.get_run_recovery(run_id)


@router.post("/radar/runs")
def create_radar_run(
    request: RadarScanRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    run = service.scan_radar(window=request.window, limit=request.limit)
    return service.inspect_radar_run(run.run_id)


@router.get("/radar/runs/{run_id}")
def inspect_radar_run(
    run_id: str,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.inspect_radar_run(run_id)


@router.get("/radar/digest/latest")
def latest_radar_digest(
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.latest_radar_digest()


@router.get("/radar/targets/{identifier}")
def inspect_radar_target(
    identifier: str,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.inspect_radar_target(identifier)


@router.get("/radar/schedule")
def show_radar_schedule(
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
    schedule_id: str | None = Query(default=None),
) -> dict[str, object]:
    return service.radar.show_schedule(schedule_id=schedule_id)


@router.get("/radar/schedule/render")
def render_radar_schedule(
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
    target: str = Query(default="windows-task"),
    schedule_id: str | None = Query(default=None),
) -> dict[str, object]:
    return service.radar.render_schedule(target=target, schedule_id=schedule_id)


@router.post("/radar/schedule/run")
def run_radar_schedule(
    request: RadarScheduleRunRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    run = service.radar.run_schedule(schedule_id=request.schedule_id)
    return service.inspect_radar_run(run.run_id)


@router.post("/radar/schedule/validate")
def validate_radar_schedule(
    request: RadarScheduleValidateRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.radar.validate_schedule_run(
        schedule_id=request.schedule_id,
        run_id=request.run_id,
        output_path=request.output_path,
    )


@router.post("/radar/candidates/replay")
def replay_radar_candidate(
    request: RadarCandidateReplayRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    run = service.replay_radar_candidate(request.candidate_id)
    return service.inspect_radar_run(run.run_id)


@router.post("/radar/promotions/rollback")
def rollback_radar_promotion(
    request: RadarPromotionRollbackRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    promotion = service.rollback_radar_promotion(request.promotion_id)
    return service.radar._serialize_promotion(promotion)


@router.get("/memory/records")
def list_memory_records(
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
    layer: list[MemoryLayer] = Query(default=[]),
    status_filter: list[RecordStatus] = Query(default=[], alias="status"),
    limit: int = Query(default=50),
) -> list[dict[str, object]]:
    layers = tuple(layer) if layer else None
    statuses = tuple(status_filter) if status_filter else None
    return service.list_memory_records(layers=layers, statuses=statuses, limit=limit)


@router.get("/memory/records/{record_id}")
def inspect_memory_record(
    record_id: str,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.inspect_memory_record(record_id)


@router.post("/memory/search")
def search_memory_records(
    request: MemorySearchRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    layers = tuple(request.layers) if request.layers else None
    statuses = tuple(request.statuses) if request.statuses else None
    return {
        "records": service.search_memory(
            query=request.query,
            layers=layers,
            statuses=statuses,
            limit=request.limit,
        )
    }


@router.get("/memory/review-queue")
def memory_review_queue(
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
    limit: int = Query(default=50),
) -> dict[str, object]:
    return {
        "records": service.list_memory_review_queue(limit=limit),
    }


@router.post("/memory/profile/proposals")
def propose_profile_memory(
    request: MemoryProfileProposalRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.propose_profile_memory(key=request.key, value=request.value, reason=request.reason)


@router.post("/memory/review/confirm")
def confirm_memory_record(
    request: MemoryReviewRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.confirm_memory_record(request.record_id)


@router.post("/memory/review/reject")
def reject_memory_record(
    request: MemoryReviewRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
    service: Annotated[TaskAgentService, Depends(get_task_agent_service)],
) -> dict[str, object]:
    return service.reject_memory_record(request.record_id)


@router.post("/commands/ack")
def acknowledge_command(
    request: CommandAckRequest,
    _bridge_key: Annotated[str, Depends(require_bridge_key)],
) -> dict[str, object]:
    return {
        "status": "ok",
        "acknowledged": request.accepted,
        "command_id": request.command_id,
        "received_at": datetime.now(UTC).isoformat(),
    }

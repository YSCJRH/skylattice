"""FastAPI application for the Skylattice task-agent runtime."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI

from skylattice import __version__
from skylattice.runtime import TaskAgentService

app = FastAPI(
    title="Skylattice",
    version=__version__,
    summary="CLI-first task agent runtime for a private evolvable agent.",
)


@lru_cache(maxsize=1)
def get_task_agent_service() -> TaskAgentService:
    return TaskAgentService.from_repo()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "skylattice",
        "version": __version__,
    }


@app.get("/kernel/summary")
def kernel_summary(service: TaskAgentService = Depends(get_task_agent_service)) -> dict[str, object]:
    return service.doctor_report()["kernel"]


@app.get("/runs/{run_id}")
def get_run(run_id: str, service: TaskAgentService = Depends(get_task_agent_service)) -> dict[str, object]:
    return service.inspect_run(run_id)["run"]


@app.get("/runs/{run_id}/events")
def get_run_events(run_id: str, service: TaskAgentService = Depends(get_task_agent_service)) -> list[dict[str, object]]:
    return service.inspect_run(run_id)["events"]


@app.get("/runs/{run_id}/memory")
def get_run_memory(run_id: str, service: TaskAgentService = Depends(get_task_agent_service)) -> list[dict[str, object]]:
    return service.inspect_run(run_id)["memory"]

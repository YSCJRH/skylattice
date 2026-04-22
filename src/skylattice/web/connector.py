"""Hosted web control-plane connector for local Skylattice runtimes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from skylattice.memory.interfaces import MemoryLayer, RecordStatus
from skylattice.runtime import TaskAgentService

from .config import WebConnectorConfig


@dataclass
class WebConnectorPairResult:
    control_plane_url: str
    device_id: str
    device_label: str
    connector_token_present: bool


class SkylatticeWebConnector:
    def __init__(
        self,
        *,
        repo_root: Path,
        service: TaskAgentService | None = None,
        config: WebConnectorConfig | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.service = service or TaskAgentService.from_repo(repo_root=self.repo_root)
        self.config = config or WebConnectorConfig.from_repo(self.repo_root)

    def status_report(self) -> dict[str, object]:
        doctor = self.service.doctor_report()
        return {
            "status": "ok",
            "connector": self.config.status_payload(),
            "bridge": self.config.bridge_auth_payload(),
            "doctor": {
                "status": doctor["status"],
                "runtime": doctor["runtime"],
                "radar": doctor["radar"],
            },
            "auth": self.service.auth_preflight_report(),
        }

    def pair(
        self,
        *,
        control_plane_url: str,
        pairing_code: str,
        device_label: str,
        bridge_base_url: str | None = None,
    ) -> dict[str, object]:
        payload = self._request_json(
            control_plane_url.rstrip("/") + "/api/control-plane/pairings/claim",
            method="POST",
            payload={
                "pairingCode": pairing_code,
                "deviceLabel": device_label,
                "bridgeBaseUrl": bridge_base_url or self.config.bridge_base_url,
            },
        )
        self.config.control_plane_url = control_plane_url.rstrip("/")
        self.config.device_id = str(payload.get("deviceId", "")).strip() or None
        self.config.device_label = str(payload.get("label", device_label)).strip() or device_label
        self.config.connector_token = str(payload.get("connectorToken", "")).strip() or None
        if bridge_base_url:
            self.config.bridge_base_url = bridge_base_url.strip()
        self.config.save()
        return {
            "status": "ok",
            "pairing": WebConnectorPairResult(
                control_plane_url=self.config.control_plane_url or control_plane_url.rstrip("/"),
                device_id=self.config.device_id or "",
                device_label=self.config.device_label or device_label,
                connector_token_present=bool(self.config.connector_token),
            ).__dict__,
            "connector": self.config.status_payload(),
        }

    def heartbeat(self) -> dict[str, object]:
        self._ensure_paired()
        payload = self._request_json(
            self.config.control_plane_url.rstrip("/") + "/api/control-plane/devices/heartbeat",
            method="POST",
            payload=self._heartbeat_payload(),
            connector_token=self.config.connector_token,
        )
        return {
            "status": "ok",
            "device": payload.get("device"),
            "connector": self.config.status_payload(),
        }

    def poll_once(self) -> dict[str, object]:
        self._ensure_paired()
        heartbeat = self.heartbeat()
        next_payload = self._request_json(
            self.config.control_plane_url.rstrip("/") + "/api/control-plane/commands/next",
            method="GET",
            connector_token=self.config.connector_token,
        )
        command = next_payload.get("command")
        if not isinstance(command, dict):
            return {
                "status": "idle",
                "heartbeat": heartbeat,
                "connector": self.config.status_payload(),
            }
        command_id = str(command.get("commandId", ""))
        try:
            result = self._execute_command(command)
            recorded = self._request_json(
                self.config.control_plane_url.rstrip("/") + f"/api/control-plane/commands/{command_id}/result",
                method="POST",
                payload={"status": "succeeded", "result": result},
                connector_token=self.config.connector_token,
            )
            return {
                "status": "ok",
                "heartbeat": heartbeat,
                "command": command,
                "result": result,
                "recorded": recorded.get("command"),
            }
        except (KeyError, RuntimeError, ValueError) as exc:
            recorded = self._request_json(
                self.config.control_plane_url.rstrip("/") + f"/api/control-plane/commands/{command_id}/result",
                method="POST",
                payload={"status": "failed", "error": str(exc)},
                connector_token=self.config.connector_token,
            )
            return {
                "status": "failed",
                "heartbeat": heartbeat,
                "command": command,
                "error": str(exc),
                "recorded": recorded.get("command"),
            }

    def _heartbeat_payload(self) -> dict[str, object]:
        doctor = self.service.doctor_report()
        auth = self.service.auth_preflight_report()
        return {
            "kernel": {"status": doctor["status"]},
            "auth": auth["auth"],
            "capabilities": auth["capabilities"],
            "connector": self.config.status_payload(),
        }

    def _execute_command(self, command: dict[str, Any]) -> dict[str, object]:
        kind = str(command.get("kind", "")).strip()
        payload = command.get("payload", {})
        if not isinstance(payload, dict):
            raise RuntimeError("Command payload must be an object.")
        if kind == "task.run":
            run = self.service.run_task(
                goal_input=str(payload.get("goal", "")),
                allow_repo_write=bool(payload.get("allowRepoWrite", False)),
                allow_destructive_repo_write=bool(payload.get("allowDestructiveRepoWrite", False)),
                allow_external_write=bool(payload.get("allowExternalWrite", False)),
            )
            return self.service.inspect_run(run.run_id)
        if kind == "task.resume":
            run = self.service.resume_task(
                run_id=str(payload.get("runId", "")),
                allow_repo_write=bool(payload.get("allowRepoWrite", False)),
                allow_destructive_repo_write=bool(payload.get("allowDestructiveRepoWrite", False)),
                allow_external_write=bool(payload.get("allowExternalWrite", False)),
            )
            return self.service.inspect_run(run.run_id)
        if kind == "radar.scan":
            run = self.service.scan_radar(
                window=str(payload.get("window", "manual")),
                limit=int(payload["limit"]) if payload.get("limit") is not None else None,
            )
            return self.service.inspect_radar_run(run.run_id)
        if kind == "radar.schedule.run":
            run = self.service.radar.run_schedule(schedule_id=self._maybe_str(payload.get("scheduleId")))
            return self.service.inspect_radar_run(run.run_id)
        if kind == "radar.schedule.validate":
            return self.service.radar.validate_schedule_run(
                schedule_id=self._maybe_str(payload.get("scheduleId")),
                run_id=self._maybe_str(payload.get("runId")),
                output_path=self._maybe_str(payload.get("outputPath")),
            )
        if kind == "radar.candidate.replay":
            run = self.service.replay_radar_candidate(str(payload.get("candidateId", "")))
            return self.service.inspect_radar_run(run.run_id)
        if kind == "radar.promotion.rollback":
            promotion = self.service.rollback_radar_promotion(str(payload.get("promotionId", "")))
            return self.service.radar._serialize_promotion(promotion)
        if kind == "memory.search":
            return {
                "records": self.service.search_memory(
                    query=str(payload.get("query", "")),
                    layers=self._coerce_layers(payload.get("layers")),
                    statuses=self._coerce_statuses(payload.get("statuses")),
                    limit=int(payload.get("limit", 5)),
                )
            }
        if kind == "memory.profile.propose":
            return self.service.propose_profile_memory(
                key=str(payload.get("key", "")),
                value=str(payload.get("value", "")),
                reason=str(payload.get("reason", "")),
            )
        if kind == "memory.review.confirm":
            return self.service.confirm_memory_record(str(payload.get("recordId", "")))
        if kind == "memory.review.reject":
            return self.service.reject_memory_record(str(payload.get("recordId", "")))
        raise RuntimeError(f"Unsupported control-plane command kind: {kind}")

    def _request_json(
        self,
        url: str,
        *,
        method: str,
        payload: dict[str, object] | None = None,
        connector_token: str | None = None,
    ) -> dict[str, object]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "skylattice-web-connector",
        }
        if connector_token:
            headers["x-skylattice-connector-token"] = connector_token
        request = Request(url, data=data, method=method, headers=headers)
        try:
            with urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw) if raw else {}
                return parsed if isinstance(parsed, dict) else {"value": parsed}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Control-plane request failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Control-plane request failed: {exc.reason}") from exc

    def _ensure_paired(self) -> None:
        if not self.config.control_plane_url or not self.config.connector_token or not self.config.device_id:
            raise RuntimeError(
                "Connector is not paired yet. Run `python -m skylattice.cli web pair --control-plane-url <url> --code <pairing-code>` first."
            )

    @staticmethod
    def _maybe_str(value: object) -> str | None:
        text = str(value or "").strip()
        return text or None

    @staticmethod
    def _coerce_layers(raw: object) -> tuple[MemoryLayer, ...] | None:
        if not isinstance(raw, list) or not raw:
            return None
        return tuple(MemoryLayer(str(item)) for item in raw)

    @staticmethod
    def _coerce_statuses(raw: object) -> tuple[RecordStatus, ...] | None:
        if not isinstance(raw, list) or not raw:
            return None
        return tuple(RecordStatus(str(item)) for item in raw)

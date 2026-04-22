"""Local configuration for the hosted web control-plane connector."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class WebConnectorConfig:
    repo_root: Path
    control_plane_url: str | None
    device_id: str | None
    connector_token: str | None
    device_label: str | None
    bridge_base_url: str
    config_path: Path

    @classmethod
    def from_repo(cls, repo_root: Path) -> "WebConnectorConfig":
        root = repo_root.resolve()
        config_path = root / ".local" / "overrides" / "web-control-plane.json"
        file_payload: dict[str, Any] = {}
        if config_path.exists():
            try:
                file_payload = json.loads(config_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                file_payload = {}
        return cls(
            repo_root=root,
            control_plane_url=str(os.environ.get("SKYLATTICE_WEB_CONTROL_PLANE_URL") or file_payload.get("control_plane_url") or "").strip() or None,
            device_id=str(os.environ.get("SKYLATTICE_WEB_DEVICE_ID") or file_payload.get("device_id") or "").strip() or None,
            connector_token=str(os.environ.get("SKYLATTICE_WEB_CONNECTOR_TOKEN") or file_payload.get("connector_token") or "").strip() or None,
            device_label=str(os.environ.get("SKYLATTICE_WEB_DEVICE_LABEL") or file_payload.get("device_label") or "").strip() or None,
            bridge_base_url=str(
                os.environ.get("SKYLATTICE_WEB_BRIDGE_BASE_URL")
                or file_payload.get("bridge_base_url")
                or "http://127.0.0.1:8000"
            ).strip(),
            config_path=config_path,
        )

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "control_plane_url": self.control_plane_url,
            "device_id": self.device_id,
            "connector_token": self.connector_token,
            "device_label": self.device_label,
            "bridge_base_url": self.bridge_base_url,
        }
        self.config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def status_payload(self) -> dict[str, object]:
        return {
            "config_path": self._display_path(self.config_path),
            "control_plane_url": self.control_plane_url,
            "device_id": self.device_id,
            "device_label": self.device_label,
            "bridge_base_url": self.bridge_base_url,
            "paired": bool(self.control_plane_url and self.device_id and self.connector_token),
            "connector_token_present": bool(self.connector_token),
        }

    def bridge_auth_payload(self) -> dict[str, object]:
        token = str(os.environ.get("SKYLATTICE_WEB_BRIDGE_KEY", "")).strip()
        return {
            "bridge_key_env_present": bool(token),
            "bridge_base_url": self.bridge_base_url,
        }

    def _display_path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.repo_root).as_posix()
        except ValueError:
            return str(path.resolve())

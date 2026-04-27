from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STARTUP_TIMEOUT_SECONDS = 90
REQUEST_TIMEOUT_SECONDS = 2
PORT_BASE = 3131
NEXT_ENV_DEV_REFERENCE = 'import "./.next/dev/types/routes.d.ts";'
NEXT_ENV_TRACKED_REFERENCE = 'import "./.next/types/routes.d.ts";'

SANITIZED_ENV_KEYS = (
    "DATABASE_URL",
    "GITHUB_ID",
    "GITHUB_SECRET",
    "NEXTAUTH_SECRET",
    "NEXTAUTH_URL",
    "NEXT_PUBLIC_SKYLATTICE_APP_URL",
    "NEXT_PUBLIC_SKYLATTICE_DEMO_PREVIEW",
    "NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL",
    "SKYLATTICE_CONTROL_PLANE_DATABASE_URL",
    "SKYLATTICE_CONTROL_PLANE_STATE_PATH",
    "SKYLATTICE_DEMO_PREVIEW",
    "SKYLATTICE_HOSTED_ALPHA",
    "VERCEL_ENV",
    "VERCEL_PROJECT_PRODUCTION_URL",
    "VERCEL_URL",
)


EMPTY_STATE: dict[str, list[Any]] = {
    "devices": [],
    "pairings": [],
    "commands": [],
    "approvals": [],
}

PAIRED_GUEST_STATE: dict[str, list[Any]] = {
    "devices": [
        {
            "deviceId": "device-local-proof",
            "userId": "guest@skylattice.local",
            "label": "Local proof connector",
            "bridgeBaseUrl": "http://127.0.0.1:8000",
            "connectorToken": "local-proof-token",
            "lastSeenAt": None,
            "online": False,
            "latestKernelStatus": None,
            "latestAuthSummary": None,
        }
    ],
    "pairings": [],
    "commands": [],
    "approvals": [],
}

COMMAND_DETAIL_STATE: dict[str, list[Any]] = {
    "devices": PAIRED_GUEST_STATE["devices"],
    "pairings": [],
    "commands": [
        {
            "commandId": "cmd-succeeded-proof",
            "userId": "guest@skylattice.local",
            "deviceId": "device-local-proof",
            "kind": "radar.schedule.validate",
            "status": "succeeded",
            "createdAt": "2026-04-27T08:00:00.000Z",
            "updatedAt": "2026-04-27T08:02:00.000Z",
            "claimedAt": "2026-04-27T08:01:00.000Z",
            "payload": {"scheduleId": "weekly-github", "window": "weekly"},
            "result": {"valid": True, "output_path": ".local/radar/validations/proof.md"},
            "error": None,
        },
        {
            "commandId": "cmd-failed-proof",
            "userId": "guest@skylattice.local",
            "deviceId": "device-local-proof",
            "kind": "task.run",
            "status": "failed",
            "createdAt": "2026-04-27T09:00:00.000Z",
            "updatedAt": "2026-04-27T09:03:00.000Z",
            "claimedAt": "2026-04-27T09:01:00.000Z",
            "payload": {"goal": "Prepare a recovery proof"},
            "result": None,
            "error": "Missing OPENAI_API_KEY; resolve local auth before retrying.",
        },
    ],
    "approvals": [
        {
            "approvalId": "approval-failed-proof",
            "userId": "guest@skylattice.local",
            "summary": "Review failed task command cmd-failed-proof",
            "requiredFlags": ["repo-write", "external-write"],
            "status": "pending",
        }
    ],
}


@dataclass(frozen=True)
class UiCase:
    name: str
    path: str
    state: dict[str, Any]
    port_hint: int
    env: dict[str, str] = field(default_factory=dict)
    must_contain: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = ()


def resolve_node() -> str:
    candidates = ("node.exe", "node") if os.name == "nt" else ("node",)
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError("Unable to locate node on PATH for the web control cockpit UI check.")


def next_cli_path() -> Path:
    path = REPO_ROOT / "node_modules" / "next" / "dist" / "bin" / "next"
    if not path.exists():
        raise FileNotFoundError("Unable to locate the repo-local Next.js CLI. Run `npm install` first.")
    return path


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        try:
            server.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def find_free_port(start: int) -> int:
    for offset in range(200):
        port = start + offset
        if port_is_free(port):
            return port
    raise RuntimeError(f"Unable to find a free localhost port starting at {start}.")


def base_env(port: int, state_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    for key in SANITIZED_ENV_KEYS:
        env.pop(key, None)
    env.update(
        {
            "NEXT_TELEMETRY_DISABLED": "1",
            "NO_COLOR": "1",
            "NEXT_PUBLIC_SKYLATTICE_APP_URL": f"http://127.0.0.1:{port}",
            "SKYLATTICE_CONTROL_PLANE_STATE_PATH": str(state_path),
        }
    )
    return env


def start_next_dev(node: str, next_cli: Path, port: int, env: dict[str, str]) -> subprocess.Popen[str]:
    command = [
        node,
        str(next_cli),
        "dev",
        "--port",
        str(port),
        "--hostname",
        "127.0.0.1",
    ]
    return subprocess.Popen(
        command,
        cwd=REPO_ROOT / "apps" / "web",
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )


def cleanup_windows_port_processes(port: int) -> None:
    repo = str(REPO_ROOT).replace("'", "''")
    script = (
        f"$repo = '{repo}'; "
        f"$port = '--port {port}'; "
        "Get-CimInstance Win32_Process -Filter \"name = 'node.exe'\" "
        "| Where-Object { $_.CommandLine -like \"*$repo*\" -and $_.CommandLine -like \"*$port*\" } "
        "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def stop_process_tree(process: subprocess.Popen[str], port: int) -> None:
    if os.name == "nt":
        if process.poll() is None:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        cleanup_windows_port_processes(port)
        return
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def fetch_when_ready(process: subprocess.Popen[str], port: int, path: str) -> str:
    url = f"http://127.0.0.1:{port}{path}"
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Next.js dev server exited early for {url} with code {process.returncode}.")
        try:
            with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return response.read().decode("utf-8", errors="ignore")
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = str(exc)
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}. Last error: {last_error}")


def assert_page_contract(case: UiCase, body: str) -> list[str]:
    errors: list[str] = []
    for phrase in case.must_contain:
        if phrase not in body:
            errors.append(f"{case.name}: expected page HTML to contain {phrase!r}.")
    for phrase in case.must_not_contain:
        if phrase in body:
            errors.append(f"{case.name}: expected page HTML not to contain {phrase!r}.")
    return errors


class NextEnvGuard:
    def __init__(self) -> None:
        self.path = REPO_ROOT / "apps" / "web" / "next-env.d.ts"
        self.existed = self.path.exists()
        self.original = self._tracked_text(self.path.read_text(encoding="utf-8")) if self.existed else ""

    @staticmethod
    def _tracked_text(text: str) -> str:
        return text.replace(NEXT_ENV_DEV_REFERENCE, NEXT_ENV_TRACKED_REFERENCE)

    def restore(self) -> None:
        if self.existed:
            current = self._tracked_text(self.path.read_text(encoding="utf-8")) if self.path.exists() else ""
            if current != self.original:
                self.path.write_text(self.original, encoding="utf-8")
            elif self.path.read_text(encoding="utf-8") != current:
                self.path.write_text(current, encoding="utf-8")
        elif self.path.exists():
            self.path.unlink()


def run_case(node: str, next_cli: Path, workspace_dir: Path, case: UiCase) -> dict[str, Any]:
    port = find_free_port(case.port_hint)
    next_env_guard = NextEnvGuard()
    with tempfile.TemporaryDirectory(prefix=f"{case.name}-", dir=workspace_dir) as temp_dir:
        state_path = Path(temp_dir) / "control-plane-state.json"
        state_path.write_text(json.dumps(case.state, indent=2) + "\n", encoding="utf-8")
        env = base_env(port, state_path)
        env.update(case.env)
        process = start_next_dev(node, next_cli, port, env)
        try:
            body = fetch_when_ready(process, port, case.path)
            errors = assert_page_contract(case, body)
            if errors:
                return {
                    "case": case.name,
                    "status": "failed",
                    "path": case.path,
                    "errors": errors,
                }
            return {
                "case": case.name,
                "status": "ok",
                "path": case.path,
                "checked": len(case.must_contain) + len(case.must_not_contain),
            }
        finally:
            stop_process_tree(process, port)
            next_env_guard.restore()


def build_cases() -> list[UiCase]:
    return [
        UiCase(
            name="preview-dashboard",
            path="/dashboard",
            state=EMPTY_STATE,
            port_hint=PORT_BASE,
            env={"NEXT_PUBLIC_SKYLATTICE_DEMO_PREVIEW": "1"},
            must_contain=(
                "Hosted Alpha control cockpit",
                "Preview is showing representative sample data.",
                "Open command center",
                "read-only",
            ),
            must_not_contain=("Hosted Alpha is blocked",),
        ),
        UiCase(
            name="hosted-alpha-blocked-dashboard",
            path="/dashboard",
            state=EMPTY_STATE,
            port_hint=PORT_BASE + 10,
            env={"SKYLATTICE_HOSTED_ALPHA": "1"},
            must_contain=(
                "Hosted Alpha is blocked",
                "Review blockers",
                "NEXT_PUBLIC_SKYLATTICE_APP_URL still points at localhost.",
                "GitHub OAuth env vars are incomplete.",
            ),
        ),
        UiCase(
            name="local-unpaired-command-center",
            path="/commands",
            state=EMPTY_STATE,
            port_hint=PORT_BASE + 20,
            must_contain=(
                "Command center",
                "Pair a local agent",
                "Local development",
                "/connect",
            ),
            must_not_contain=("Queue task intent",),
        ),
        UiCase(
            name="paired-guest-task-workspace",
            path="/tasks",
            state=PAIRED_GUEST_STATE,
            port_hint=PORT_BASE + 30,
            must_contain=(
                "Sign-in required",
                "GitHub sign-in is required",
                "Local proof connector",
                "Queue task command",
                "disabled",
            ),
            must_not_contain=("local-proof-token",),
        ),
        UiCase(
            name="succeeded-command-detail",
            path="/commands/cmd-succeeded-proof",
            state=COMMAND_DETAIL_STATE,
            port_hint=PORT_BASE + 40,
            must_contain=(
                "Command cmd-succeeded-proof",
                "Lifecycle",
                "Claimed by local connector",
                "Result recorded",
                "Command completed.",
                "Payload",
                "Result",
                "device-local-proof",
                ".local/radar/validations/proof.md",
            ),
            must_not_contain=("local-proof-token",),
        ),
        UiCase(
            name="failed-command-detail",
            path="/commands/cmd-failed-proof",
            state=COMMAND_DETAIL_STATE,
            port_hint=PORT_BASE + 50,
            must_contain=(
                "Command cmd-failed-proof",
                "failed",
                "Failed with local pressure",
                "Next safe action",
                "Review the failure before retrying.",
                "Open approvals",
                "Missing OPENAI_API_KEY; resolve local auth before retrying.",
            ),
            must_not_contain=("local-proof-token",),
        ),
    ]


def main() -> int:
    node = resolve_node()
    next_cli = next_cli_path()
    workspace_dir = REPO_ROOT / ".local" / "work" / "control-cockpit-ui"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    results = [run_case(node, next_cli, workspace_dir, case) for case in build_cases()]
    failures = [result for result in results if result["status"] != "ok"]
    payload = {
        "status": "failed" if failures else "ok",
        "scope": "local server-rendered UI contract",
        "liveHostedAlpha": "not exercised",
        "cases": results,
    }
    print(json.dumps(payload, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_hosted_alpha_env_and_store_refuse_silent_local_file_fallback() -> None:
    env_text = _read("apps/web/lib/env.ts")
    store_text = _read("apps/web/lib/control-plane/store.ts")
    blocked_store = _read("apps/web/lib/control-plane/blocked-store.ts")
    route_helpers = _read("apps/web/lib/control-plane/route-helpers.ts")

    assert "isHostedAlphaEnvironment" in env_text
    assert "requiresHostedAlphaPersistence" in env_text
    assert "hostedAlphaReadiness" in env_text
    assert "BlockedControlPlaneStore" in store_text
    assert "Hosted Alpha requires Neon/Postgres-backed control-plane state" in store_text
    assert 'backend: "blocked"' in blocked_store
    assert '"status": "blocked"' not in route_helpers
    assert 'status: "blocked"' in route_helpers
    assert "{ status: 503 }" in route_helpers


def test_control_plane_routes_use_blocked_route_helper() -> None:
    files = [
        "apps/web/app/api/control-plane/commands/route.ts",
        "apps/web/app/api/control-plane/commands/next/route.ts",
        "apps/web/app/api/control-plane/commands/[commandId]/route.ts",
        "apps/web/app/api/control-plane/commands/[commandId]/result/route.ts",
        "apps/web/app/api/control-plane/devices/route.ts",
        "apps/web/app/api/control-plane/devices/[deviceId]/route.ts",
        "apps/web/app/api/control-plane/devices/heartbeat/route.ts",
        "apps/web/app/api/control-plane/pairings/route.ts",
        "apps/web/app/api/control-plane/pairings/claim/route.ts",
        "apps/web/app/api/control-plane/approvals/route.ts",
        "apps/web/app/api/control-plane/approvals/[approvalId]/resolve/route.ts",
    ]

    for relative_path in files:
        text = _read(relative_path)
        assert "getRoutableControlPlaneStore" in text, relative_path
        assert '"response" in routed' in text, relative_path


def test_public_browser_surfaces_strip_connector_tokens() -> None:
    public_text = _read("apps/web/lib/control-plane/public.ts")
    devices_route = _read("apps/web/app/api/control-plane/devices/route.ts")
    pairings_route = _read("apps/web/app/api/control-plane/pairings/route.ts")
    dashboard_page = _read("apps/web/app/dashboard/page.tsx")
    connect_page = _read("apps/web/app/connect/page.tsx")
    devices_page = _read("apps/web/app/devices/page.tsx")
    panels = _read("apps/web/components/control-plane-panels.tsx")

    assert "connectorToken: _connectorToken" in public_text
    assert "toPublicDevices" in devices_route
    assert "toPublicPairings" in pairings_route
    assert "toPublicDevices" in dashboard_page
    assert "toPublicDevices" in connect_page
    assert "toPublicPairings" in connect_page
    assert "toPublicDevices" in devices_page
    assert "PublicPairedDevice" in panels
    assert "PublicPairingChallenge" in panels
    assert "connectorToken" not in panels


def test_postgres_identity_and_bootstrap_contract_are_tracked() -> None:
    auth_text = _read("apps/web/lib/auth.ts")
    schema_text = _read("apps/web/lib/control-plane/schema.ts")
    bootstrap_sql = _read("apps/web/sql/hosted-alpha-bootstrap.sql")
    env_example = _read("apps/web/.env.example")
    package_json = _read("package.json")
    check_script = _read("tools/check_hosted_alpha_setup.mjs")
    bootstrap_script = _read("tools/bootstrap_hosted_alpha_db.mjs")
    first_run_script = _read("tools/check_hosted_alpha_first_run_local.py")
    cockpit_script = _read("tools/check_web_control_cockpit_ui.py")
    connector_roundtrip_script = _read("tools/check_web_connector_roundtrip_local.py")
    recovery_roundtrip_script = _read("tools/check_web_connector_recovery_local.py")
    proof_suite_script = _read("tools/check_web_local_proof_suite.py")

    assert 'id = `github:${token.sub}`' in auth_text
    assert 'text("user_id")' in schema_text
    assert "create table if not exists control_plane_users" in bootstrap_sql
    assert "create table if not exists paired_devices" in bootstrap_sql
    assert "create table if not exists pairing_challenges" in bootstrap_sql
    assert "create table if not exists command_requests" in bootstrap_sql
    assert "create table if not exists approval_records" in bootstrap_sql
    assert "SKYLATTICE_HOSTED_ALPHA=1" in env_example
    assert "DATABASE_URL=" in env_example
    assert '"web:hosted-alpha:check"' in package_json
    assert '"web:hosted-alpha:bootstrap"' in package_json
    assert '"web:first-run:local"' in package_json
    assert '"web:cockpit:check"' in package_json
    assert '"web:connector:local"' in package_json
    assert '"web:recovery:local"' in package_json
    assert '"web:proof:local"' in package_json
    assert "Hosted Alpha mode is not active" in check_script
    assert "DATABASE_URL or SKYLATTICE_CONTROL_PLANE_DATABASE_URL is missing." in check_script
    assert "hosted-alpha-bootstrap.sql" in bootstrap_script
    assert "status: \"ok\"" in bootstrap_script
    assert "Connector is not paired yet" in first_run_script
    assert "Local Hosted Alpha readiness check unexpectedly passed." in first_run_script
    assert "local server-rendered UI contract" in cockpit_script
    assert "liveHostedAlpha" in cockpit_script
    assert "cmd-succeeded-proof" in cockpit_script
    assert "cmd-failed-proof" in cockpit_script
    assert "local-proof-token" in cockpit_script
    assert "local connector HTTP roundtrip" in connector_roundtrip_script
    assert "cmd-local-memory-search" in connector_roundtrip_script
    assert "memory.search" in connector_roundtrip_script
    assert "local connector recovery roundtrip" in recovery_roundtrip_script
    assert "cmd-local-recovery-proof" in recovery_roundtrip_script
    assert "approvalPressureRecorded" in recovery_roundtrip_script
    assert "local Hosted Alpha proof suite" in proof_suite_script
    assert "check_web_connector_recovery_local.py" in proof_suite_script


def test_docs_distinguish_preview_hosted_alpha_and_local_agent() -> None:
    index_page = _read("docs/index.md")
    app_preview = _read("docs/app-preview.md")
    web_control_plane = _read("docs/web-control-plane.md")
    runbook = _read("docs/ops/hosted-alpha-runbook.md")
    first_run_note = _read("docs/ops/hosted-alpha-validations/2026-04-27-first-run-proof-loop.md")
    readme = _read("README.md")
    web_readme = _read("apps/web/README.md")
    quickstart = _read("docs/quickstart.md")
    layout = _read("apps/web/app/layout.tsx")
    mode_helper = _read("apps/web/lib/control-plane/mode.ts")
    dashboard = _read("apps/web/app/dashboard/page.tsx")
    commands = _read("apps/web/app/commands/page.tsx")
    task_brief = _read("docs/tasks/hosted-alpha-control-cockpit.md")
    first_run_task_brief = _read("docs/tasks/hosted-alpha-first-run-proof-loop.md")

    assert "Preview and live Hosted Alpha are intentionally separate" in index_page
    assert "Hosted Alpha" in app_preview
    assert "Docs" in web_control_plane
    assert "Preview" in web_control_plane
    assert "Hosted Alpha" in web_control_plane
    assert "Local Agent" in web_control_plane
    assert "Hosted Alpha means:" in runbook
    assert "Hosted Alpha does **not** mean:" in runbook
    assert "Hosted Alpha Launch" in runbook
    assert "Skylattice Hosted Alpha" in runbook
    assert "docs/ops/hosted-alpha-validations/" in runbook
    assert "Hosted Alpha First-Run Proof Loop Validation" in first_run_note
    assert "Connector is not paired yet" in first_run_note
    assert "npm run web:first-run:local" in runbook
    assert "npm run web:first-run:local" in first_run_note
    assert "npm run web:cockpit:check" in runbook
    assert "npm run web:cockpit:check" in first_run_task_brief
    assert "npm run web:cockpit:check" in first_run_note
    assert "npm run web:connector:local" in runbook
    assert "npm run web:connector:local" in first_run_task_brief
    assert "npm run web:connector:local" in first_run_note
    assert "npm run web:recovery:local" in runbook
    assert "npm run web:recovery:local" in first_run_task_brief
    assert "npm run web:recovery:local" in first_run_note
    assert "npm run web:proof:local" in runbook
    assert "npm run web:proof:local" in first_run_task_brief
    assert "npm run web:proof:local" in first_run_note
    assert "local UI contract check only" in first_run_note
    assert "succeeded and failed command detail pages" in first_run_note
    assert "connector protocol roundtrip locally" in first_run_note
    assert "npm run web:first-run:local" in readme
    assert "npm run web:first-run:local" in web_readme
    assert "npm run web:first-run:local" in quickstart
    assert "npm run web:cockpit:check" in readme
    assert "npm run web:cockpit:check" in web_readme
    assert "npm run web:connector:local" in readme
    assert "npm run web:connector:local" in web_readme
    assert "npm run web:recovery:local" in readme
    assert "npm run web:recovery:local" in web_readme
    assert "npm run web:proof:local" in readme
    assert "npm run web:proof:local" in web_readme
    assert "succeeded/failed command-detail" in readme
    assert "succeeded/failed command-detail" in web_readme
    assert "local Hosted Alpha first-run proof loop" in readme
    assert "without pretending local development is a live deployment" in web_readme
    assert "control cockpit" in app_preview
    assert "Control Cockpit Shape" in web_control_plane
    assert "Command center" in commands
    assert "Hosted Alpha control cockpit" in dashboard
    assert 'export type ControlPlaneMode = "preview" | "blocked" | "development" | "live-unpaired" | "live-ready"' in mode_helper
    assert "Sign-in required" in mode_helper
    assert "signInRequired" in _read("apps/web/components/control-plane-panels.tsx")
    assert "signedIn" in _read("apps/web/lib/control-plane/page-context.ts")
    assert "/commands` is the product center" in task_brief
    assert "unauthenticated paired states" in task_brief
    assert "This is the local development control plane." in layout
    assert "Hosted Alpha can route intent to paired local agents." in layout
    assert "Preview is showing representative sample data." in layout


def test_web_workspace_uses_repo_local_font_assets_for_build_stability() -> None:
    layout = _read("apps/web/app/layout.tsx")
    globals_css = _read("apps/web/app/globals.css")
    package_json = _read("apps/web/package.json")

    assert "next/font/google" not in layout
    assert '@fontsource/outfit/700.css' in globals_css
    assert '@fontsource/plus-jakarta-sans/400.css' in globals_css
    assert '"@fontsource/outfit"' in package_json
    assert '"@fontsource/plus-jakarta-sans"' in package_json

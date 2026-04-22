import type { ApprovalRecord, CommandRecord, DashboardSnapshot, PairedDevice, PairingChallenge } from "@/lib/control-plane/types";
import { DOCS_URL } from "@/lib/env";

export const DEMO_GUEST_USER_ID = "guest@skylattice.local";

const DEMO_DEVICES: PairedDevice[] = [
  {
    deviceId: "device-demo-primary",
    userId: DEMO_GUEST_USER_ID,
    label: "Primary workstation",
    bridgeBaseUrl: "http://127.0.0.1:8000",
    connectorToken: "demo-token-primary",
    lastSeenAt: "2026-04-22T10:45:00Z",
    online: true,
    latestKernelStatus: "ok",
    latestAuthSummary: "GitHub bridge is available from gh; OpenAI and GitLab live credentials are still missing.",
  },
  {
    deviceId: "device-demo-lab",
    userId: DEMO_GUEST_USER_ID,
    label: "Lab laptop",
    bridgeBaseUrl: "http://127.0.0.1:8000",
    connectorToken: "demo-token-lab",
    lastSeenAt: "2026-04-22T08:10:00Z",
    online: false,
    latestKernelStatus: "ok",
    latestAuthSummary: "Last heartbeat came from a local runtime without live provider credentials configured.",
  },
];

const DEMO_PAIRINGS: PairingChallenge[] = [
  {
    pairingId: "pairing-demo-claimed",
    userId: DEMO_GUEST_USER_ID,
    pairingCode: "PAIRDEMO",
    createdAt: "2026-04-22T10:20:00Z",
    expiresAt: "2026-04-22T10:35:00Z",
    claimedAt: "2026-04-22T10:24:00Z",
    deviceId: "device-demo-primary",
    deviceLabel: "Primary workstation",
    connectorToken: "demo-token-primary",
  },
  {
    pairingId: "pairing-demo-pending",
    userId: DEMO_GUEST_USER_ID,
    pairingCode: "TRYDEMO",
    createdAt: "2026-04-22T10:48:00Z",
    expiresAt: "2026-04-22T11:03:00Z",
    claimedAt: null,
    deviceId: null,
    deviceLabel: null,
    connectorToken: null,
  },
];

const DEMO_COMMANDS: CommandRecord[] = [
  {
    commandId: "cmd-demo-task-run",
    userId: DEMO_GUEST_USER_ID,
    deviceId: "device-demo-primary",
    kind: "task.run",
    status: "succeeded",
    createdAt: "2026-04-22T10:05:00Z",
    updatedAt: "2026-04-22T10:08:00Z",
    claimedAt: "2026-04-22T10:05:20Z",
    payload: {
      goal: "Refresh the README and prepare a draft PR for the hosted control plane.",
      allowRepoWrite: true,
      allowExternalWrite: false,
    },
    result: {
      run: {
        run_id: "run-demo-1",
        status: "completed",
        branch_name: "codex/demo-web-proof",
      },
      validation: {
        profile: "baseline",
        passed: true,
      },
    },
    error: null,
  },
  {
    commandId: "cmd-demo-radar-scan",
    userId: DEMO_GUEST_USER_ID,
    deviceId: "device-demo-primary",
    kind: "radar.scan",
    status: "succeeded",
    createdAt: "2026-04-22T09:30:00Z",
    updatedAt: "2026-04-22T09:36:00Z",
    claimedAt: "2026-04-22T09:30:12Z",
    payload: {
      window: "weekly",
      limit: 20,
    },
    result: {
      run: {
        run_id: "radar-demo-1",
        promoted: false,
        candidate_count: 6,
      },
    },
    error: null,
  },
  {
    commandId: "cmd-demo-radar-validate",
    userId: DEMO_GUEST_USER_ID,
    deviceId: "device-demo-primary",
    kind: "radar.schedule.validate",
    status: "succeeded",
    createdAt: "2026-04-22T09:40:00Z",
    updatedAt: "2026-04-22T09:41:00Z",
    claimedAt: "2026-04-22T09:40:11Z",
    payload: {
      scheduleId: "weekly-github",
    },
    result: {
      valid: true,
      output_path: ".local/radar/validations/2026-04-22-weekly-github.json",
    },
    error: null,
  },
  {
    commandId: "cmd-demo-memory-search",
    userId: DEMO_GUEST_USER_ID,
    deviceId: "device-demo-primary",
    kind: "memory.search",
    status: "succeeded",
    createdAt: "2026-04-22T10:12:00Z",
    updatedAt: "2026-04-22T10:12:05Z",
    claimedAt: "2026-04-22T10:12:01Z",
    payload: {
      query: "governance",
      limit: 5,
    },
    result: {
      records: [
        { record_id: "mem-demo-1", kind: "semantic" },
        { record_id: "mem-demo-2", kind: "procedural" },
      ],
    },
    error: null,
  },
  {
    commandId: "cmd-demo-memory-proposal",
    userId: DEMO_GUEST_USER_ID,
    deviceId: "device-demo-primary",
    kind: "memory.profile.propose",
    status: "claimed",
    createdAt: "2026-04-22T10:42:00Z",
    updatedAt: "2026-04-22T10:43:00Z",
    claimedAt: "2026-04-22T10:42:10Z",
    payload: {
      key: "operator_style",
      value: "concise, architecture-first",
      reason: "Keep the hosted preview aligned with the repo voice.",
    },
    result: {
      note: "Awaiting local review completion.",
    },
    error: null,
  },
  {
    commandId: "cmd-demo-task-resume",
    userId: DEMO_GUEST_USER_ID,
    deviceId: "device-demo-primary",
    kind: "task.resume",
    status: "failed",
    createdAt: "2026-04-22T10:16:00Z",
    updatedAt: "2026-04-22T10:17:00Z",
    claimedAt: "2026-04-22T10:16:08Z",
    payload: {
      runId: "run-demo-blocked",
      allowExternalWrite: false,
    },
    result: {
      run: {
        run_id: "run-demo-blocked",
        status: "blocked",
      },
    },
    error: "Local runtime blocked external-write until the operator grants the required approval.",
  },
];

const DEMO_APPROVALS: ApprovalRecord[] = [
  {
    approvalId: "approval-demo-external-write",
    userId: DEMO_GUEST_USER_ID,
    summary: "Review blocked task.resume command cmd-demo-task-resume before allowing external-write.",
    requiredFlags: ["repo-write", "external-write"],
    status: "pending",
  },
];

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export function getDemoDevices(): PairedDevice[] {
  return clone(DEMO_DEVICES);
}

export function getDemoPairings(): PairingChallenge[] {
  return clone(DEMO_PAIRINGS);
}

export function getDemoCommands(): CommandRecord[] {
  return clone(DEMO_COMMANDS);
}

export function getDemoApprovals(): ApprovalRecord[] {
  return clone(DEMO_APPROVALS);
}

export function getDemoCommand(commandId: string): CommandRecord {
  const command = DEMO_COMMANDS.find((item) => item.commandId === commandId);
  if (!command) {
    throw new Error("Command is unknown for the preview surface.");
  }
  return clone(command);
}

export function getDemoDashboardSnapshot(): DashboardSnapshot {
  const commands = getDemoCommands()
    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
    .slice(0, 12);
  return {
    backend: "local-file",
    userId: DEMO_GUEST_USER_ID,
    docsUrl: DOCS_URL,
    devices: getDemoDevices(),
    pairings: getDemoPairings(),
    commands,
    pendingApprovals: getDemoApprovals(),
    memoryReviewCount: commands.filter((command) => command.kind.startsWith("memory.") && command.status !== "failed").length,
  };
}

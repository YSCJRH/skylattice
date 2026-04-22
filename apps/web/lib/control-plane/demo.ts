import previewState from "../../../../examples/redacted/web-app-preview-state.json";

import type { ApprovalRecord, CommandRecord, DashboardSnapshot, PairedDevice, PairingChallenge } from "@/lib/control-plane/types";
import { DOCS_URL } from "@/lib/env";

export const DEMO_GUEST_USER_ID = "guest@skylattice.local";

type DemoPreviewState = {
  devices: PairedDevice[];
  pairings: PairingChallenge[];
  commands: CommandRecord[];
  approvals: ApprovalRecord[];
};

const DEMO_PREVIEW_STATE = previewState as DemoPreviewState;

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export function getDemoDevices(): PairedDevice[] {
  return clone(DEMO_PREVIEW_STATE.devices);
}

export function getDemoPairings(): PairingChallenge[] {
  return clone(DEMO_PREVIEW_STATE.pairings);
}

export function getDemoCommands(): CommandRecord[] {
  return clone(DEMO_PREVIEW_STATE.commands);
}

export function getDemoApprovals(): ApprovalRecord[] {
  return clone(DEMO_PREVIEW_STATE.approvals);
}

export function getDemoCommand(commandId: string): CommandRecord {
  const command = DEMO_PREVIEW_STATE.commands.find((item) => item.commandId === commandId);
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

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";

import { APP_BASE_URL, DOCS_URL, controlPlaneDatabaseUrl } from "@/lib/env";
import { DEFAULT_STATE, newExpiry, nowIso, summarizeAuth, upsertPendingApproval } from "@/lib/control-plane/helpers";
import { PostgresControlPlaneStore } from "@/lib/control-plane/postgres-store";
import type {
  ApprovalRecord,
  CommandKind,
  CommandRecord,
  ControlPlaneState,
  ControlPlaneStore,
  DashboardSnapshot,
  PairedDevice,
  PairingChallenge,
} from "@/lib/control-plane/types";

function repoStatePath(): string {
  const configured = process.env.SKYLATTICE_CONTROL_PLANE_STATE_PATH;
  if (configured) {
    return configured;
  }
  return path.resolve(process.cwd(), "../../.local/state/web-control-plane.json");
}

export class LocalFileControlPlaneStore implements ControlPlaneStore {
  constructor(private readonly statePath: string = repoStatePath()) {}

  private async load(): Promise<ControlPlaneState> {
    await mkdir(path.dirname(this.statePath), { recursive: true });
    try {
      const raw = await readFile(this.statePath, "utf-8");
      return { ...DEFAULT_STATE, ...(JSON.parse(raw) as ControlPlaneState) };
    } catch {
      await this.save(DEFAULT_STATE);
      return { ...DEFAULT_STATE };
    }
  }

  private async save(state: ControlPlaneState): Promise<void> {
    await mkdir(path.dirname(this.statePath), { recursive: true });
    await writeFile(this.statePath, JSON.stringify(state, null, 2) + "\n", "utf-8");
  }

  async getDashboardSnapshot(userId: string): Promise<DashboardSnapshot> {
    const state = await this.load();
    const devices = state.devices.filter((device) => device.userId === userId);
    const pairings = state.pairings.filter((pairing) => pairing.userId === userId);
    const commands = state.commands
      .filter((command) => command.userId === userId)
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
      .slice(0, 12);
    const pendingApprovals = state.approvals.filter(
      (approval) => approval.userId === userId && approval.status === "pending",
    );
    return {
      backend: "local-file",
      userId,
      docsUrl: DOCS_URL,
      devices,
      pairings,
      commands,
      pendingApprovals,
      memoryReviewCount: commands.filter((command) => command.kind.startsWith("memory.") && command.status !== "failed").length,
    };
  }

  async listDevices(userId: string): Promise<PairedDevice[]> {
    const state = await this.load();
    return state.devices.filter((device) => device.userId === userId);
  }

  async listApprovals(userId: string): Promise<ApprovalRecord[]> {
    const state = await this.load();
    return state.approvals.filter((approval) => approval.userId === userId);
  }

  async listCommands(userId: string): Promise<CommandRecord[]> {
    const state = await this.load();
    return state.commands.filter((command) => command.userId === userId);
  }

  async getCommand(userId: string, commandId: string): Promise<CommandRecord> {
    const state = await this.load();
    const command = state.commands.find((item) => item.userId === userId && item.commandId === commandId);
    if (!command) {
      throw new Error("Command is unknown for the current user.");
    }
    return command;
  }

  async createPairingChallenge(userId: string): Promise<PairingChallenge> {
    const state = await this.load();
    const challenge: PairingChallenge = {
      pairingId: randomUUID(),
      userId,
      pairingCode: randomUUID().replace(/-/g, "").slice(0, 8).toUpperCase(),
      createdAt: nowIso(),
      expiresAt: newExpiry(15),
      claimedAt: null,
      deviceId: null,
      deviceLabel: null,
      connectorToken: null,
    };
    state.pairings.push(challenge);
    await this.save(state);
    return challenge;
  }

  async claimPairing(pairingCode: string, deviceLabel: string, bridgeBaseUrl: string): Promise<PairedDevice> {
    const state = await this.load();
    const challenge = state.pairings.find(
      (item) =>
        item.pairingCode === pairingCode.trim().toUpperCase()
        && item.claimedAt === null
        && item.expiresAt > nowIso(),
    );
    if (!challenge) {
      throw new Error("Pairing code is unknown, expired, or already claimed.");
    }
    const connectorToken = randomUUID();
    const device: PairedDevice = {
      deviceId: randomUUID(),
      userId: challenge.userId,
      label: deviceLabel.trim() || "Local Skylattice Agent",
      bridgeBaseUrl: bridgeBaseUrl.trim() || "http://127.0.0.1:8000",
      connectorToken,
      lastSeenAt: null,
      online: false,
      latestKernelStatus: null,
      latestAuthSummary: null,
    };
    challenge.claimedAt = nowIso();
    challenge.deviceId = device.deviceId;
    challenge.deviceLabel = device.label;
    challenge.connectorToken = connectorToken;
    state.devices.push(device);
    await this.save(state);
    return device;
  }

  async revokeDevice(userId: string, deviceId: string): Promise<{ revoked: boolean; deviceId: string }> {
    const state = await this.load();
    const before = state.devices.length;
    state.devices = state.devices.filter((device) => !(device.userId === userId && device.deviceId === deviceId));
    if (state.devices.length == before) {
      throw new Error("Device is unknown for the current user.");
    }
    state.commands = state.commands.map((command) =>
      command.deviceId === deviceId && command.status === "queued"
        ? { ...command, deviceId: null, updatedAt: nowIso() }
        : command,
    );
    await this.save(state);
    return { revoked: true, deviceId };
  }

  async queueCommand(userId: string, kind: CommandKind, payload: Record<string, unknown>, deviceId?: string | null): Promise<CommandRecord> {
    const state = await this.load();
    const effectiveDeviceId = deviceId || state.devices.find((device) => device.userId === userId)?.deviceId || null;
    const command: CommandRecord = {
      commandId: randomUUID(),
      userId,
      deviceId: effectiveDeviceId,
      kind,
      status: "queued",
      createdAt: nowIso(),
      updatedAt: nowIso(),
      claimedAt: null,
      payload,
      result: null,
      error: null,
    };
    state.commands.push(command);
    await this.save(state);
    return command;
  }

  async claimNextCommand(connectorToken: string): Promise<CommandRecord | null> {
    const state = await this.load();
    const device = state.devices.find((item) => item.connectorToken === connectorToken);
    if (!device) {
      throw new Error("Connector token is not paired to a device.");
    }
    const command = state.commands.find(
      (item) => item.status === "queued" && (!item.deviceId || item.deviceId === device.deviceId),
    );
    if (!command) {
      return null;
    }
    command.status = "claimed";
    command.claimedAt = nowIso();
    command.updatedAt = nowIso();
    command.deviceId = device.deviceId;
    await this.save(state);
    return command;
  }

  async recordHeartbeat(connectorToken: string, payload: Record<string, unknown>): Promise<PairedDevice> {
    const state = await this.load();
    const device = state.devices.find((item) => item.connectorToken === connectorToken);
    if (!device) {
      throw new Error("Connector token is not paired to a device.");
    }
    device.lastSeenAt = nowIso();
    device.online = true;
    const kernel = payload.kernel;
    if (kernel && typeof kernel === "object") {
      device.latestKernelStatus = String((kernel as Record<string, unknown>).status || "ok");
    } else {
      device.latestKernelStatus = "ok";
    }
    device.latestAuthSummary = summarizeAuth(payload);
    await this.save(state);
    return device;
  }

  async recordCommandResult(
    connectorToken: string,
    commandId: string,
    payload: { status: "succeeded" | "failed"; result?: Record<string, unknown>; error?: string | null },
  ): Promise<CommandRecord> {
    const state = await this.load();
    const device = state.devices.find((item) => item.connectorToken === connectorToken);
    if (!device) {
      throw new Error("Connector token is not paired to a device.");
    }
    const command = state.commands.find((item) => item.commandId === commandId && item.deviceId === device.deviceId);
    if (!command) {
      throw new Error("Command is unknown for the current device.");
    }
    command.status = payload.status;
    command.updatedAt = nowIso();
    command.result = payload.result || null;
    command.error = payload.error || null;
    device.lastSeenAt = nowIso();
    device.online = true;
    if (command.status === "failed") {
      state.approvals = upsertPendingApproval(
        state.approvals,
        command.userId,
        `Review failed ${command.kind} command ${command.commandId}`,
        ["repo-write", "external-write"],
      );
    }
    await this.save(state);
    return command;
  }

  async resolveApproval(userId: string, approvalId: string): Promise<ApprovalRecord> {
    const state = await this.load();
    const approval = state.approvals.find((item) => item.userId === userId && item.approvalId === approvalId);
    if (!approval) {
      throw new Error("Approval is unknown for the current user.");
    }
    approval.status = "resolved";
    await this.save(state);
    return approval;
  }

  describePersistence(): { backend: "local-file"; statePath: string; appBaseUrl: string } {
    return {
      backend: "local-file",
      statePath: this.statePath,
      appBaseUrl: APP_BASE_URL,
    };
  }
}

export function getControlPlaneStore(): ControlPlaneStore {
  if (controlPlaneDatabaseUrl()) {
    return new PostgresControlPlaneStore();
  }
  return new LocalFileControlPlaneStore();
}

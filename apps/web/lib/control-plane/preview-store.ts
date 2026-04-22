import type {
  ApprovalRecord,
  CommandKind,
  CommandRecord,
  ControlPlaneStore,
  DashboardSnapshot,
  PairedDevice,
  PairingChallenge,
} from "@/lib/control-plane/types";
import {
  DEMO_GUEST_USER_ID,
  getDemoApprovals,
  getDemoCommand,
  getDemoCommands,
  getDemoDashboardSnapshot,
  getDemoDevices,
} from "@/lib/control-plane/demo";
import { isDemoPreviewEnabled } from "@/lib/env";

function previewBlocked(action: string): never {
  throw new Error(`Preview mode is read-only. Sign in with GitHub before ${action}.`);
}

function isPreviewUser(userId: string): boolean {
  return isDemoPreviewEnabled() && userId === DEMO_GUEST_USER_ID;
}

export class PreviewControlPlaneStore implements ControlPlaneStore {
  constructor(private readonly base: ControlPlaneStore) {}

  async getDashboardSnapshot(userId: string): Promise<DashboardSnapshot> {
    if (isPreviewUser(userId)) {
      return {
        ...getDemoDashboardSnapshot(),
        backend: this.base.describePersistence().backend,
      };
    }
    return this.base.getDashboardSnapshot(userId);
  }

  async listDevices(userId: string): Promise<PairedDevice[]> {
    if (isPreviewUser(userId)) {
      return getDemoDevices();
    }
    return this.base.listDevices(userId);
  }

  async listApprovals(userId: string): Promise<ApprovalRecord[]> {
    if (isPreviewUser(userId)) {
      return getDemoApprovals();
    }
    return this.base.listApprovals(userId);
  }

  async listCommands(userId: string): Promise<CommandRecord[]> {
    if (isPreviewUser(userId)) {
      return getDemoCommands();
    }
    return this.base.listCommands(userId);
  }

  async getCommand(userId: string, commandId: string): Promise<CommandRecord> {
    if (isPreviewUser(userId)) {
      return getDemoCommand(commandId);
    }
    return this.base.getCommand(userId, commandId);
  }

  async createPairingChallenge(userId: string): Promise<PairingChallenge> {
    if (isPreviewUser(userId)) {
      return previewBlocked("creating a pairing code");
    }
    return this.base.createPairingChallenge(userId);
  }

  async claimPairing(pairingCode: string, deviceLabel: string, bridgeBaseUrl: string): Promise<PairedDevice> {
    return this.base.claimPairing(pairingCode, deviceLabel, bridgeBaseUrl);
  }

  async revokeDevice(userId: string, deviceId: string): Promise<{ revoked: boolean; deviceId: string }> {
    if (isPreviewUser(userId)) {
      return previewBlocked("revoking a device");
    }
    return this.base.revokeDevice(userId, deviceId);
  }

  async queueCommand(
    userId: string,
    kind: CommandKind,
    payload: Record<string, unknown>,
    deviceId?: string | null,
  ): Promise<CommandRecord> {
    if (isPreviewUser(userId)) {
      return previewBlocked(`queueing ${kind}`);
    }
    return this.base.queueCommand(userId, kind, payload, deviceId);
  }

  async claimNextCommand(connectorToken: string): Promise<CommandRecord | null> {
    return this.base.claimNextCommand(connectorToken);
  }

  async recordHeartbeat(connectorToken: string, payload: Record<string, unknown>): Promise<PairedDevice> {
    return this.base.recordHeartbeat(connectorToken, payload);
  }

  async recordCommandResult(
    connectorToken: string,
    commandId: string,
    payload: { status: "succeeded" | "failed"; result?: Record<string, unknown>; error?: string | null },
  ): Promise<CommandRecord> {
    return this.base.recordCommandResult(connectorToken, commandId, payload);
  }

  async resolveApproval(userId: string, approvalId: string): Promise<ApprovalRecord> {
    if (isPreviewUser(userId)) {
      return previewBlocked("resolving approval reminders");
    }
    return this.base.resolveApproval(userId, approvalId);
  }

  describePersistence(): { backend: "local-file" | "postgres"; statePath: string; appBaseUrl: string } {
    return this.base.describePersistence();
  }
}

import { APP_BASE_URL, DOCS_URL } from "@/lib/env";
import type {
  ApprovalRecord,
  CommandKind,
  CommandRecord,
  ControlPlaneStore,
  DashboardSnapshot,
  PairedDevice,
  PairingChallenge,
} from "@/lib/control-plane/types";

function unavailable(reason: string): never {
  throw new Error(reason);
}

export class BlockedControlPlaneStore implements ControlPlaneStore {
  constructor(private readonly reason: string) {}

  private emptySnapshot(userId: string): DashboardSnapshot {
    return {
      backend: "blocked",
      userId,
      docsUrl: DOCS_URL,
      devices: [],
      pairings: [],
      commands: [],
      pendingApprovals: [],
      memoryReviewCount: 0,
    };
  }

  async getDashboardSnapshot(userId: string): Promise<DashboardSnapshot> {
    return this.emptySnapshot(userId);
  }

  async listDevices(_userId: string): Promise<PairedDevice[]> {
    unavailable(this.reason);
  }

  async listApprovals(_userId: string): Promise<ApprovalRecord[]> {
    unavailable(this.reason);
  }

  async listCommands(_userId: string): Promise<CommandRecord[]> {
    unavailable(this.reason);
  }

  async getCommand(_userId: string, _commandId: string): Promise<CommandRecord> {
    unavailable(this.reason);
  }

  async createPairingChallenge(_userId: string): Promise<PairingChallenge> {
    unavailable(this.reason);
  }

  async claimPairing(_pairingCode: string, _deviceLabel: string, _bridgeBaseUrl: string): Promise<PairedDevice> {
    unavailable(this.reason);
  }

  async revokeDevice(_userId: string, _deviceId: string): Promise<{ revoked: boolean; deviceId: string }> {
    unavailable(this.reason);
  }

  async queueCommand(
    _userId: string,
    _kind: CommandKind,
    _payload: Record<string, unknown>,
    _deviceId?: string | null,
  ): Promise<CommandRecord> {
    unavailable(this.reason);
  }

  async claimNextCommand(_connectorToken: string): Promise<CommandRecord | null> {
    unavailable(this.reason);
  }

  async recordHeartbeat(_connectorToken: string, _payload: Record<string, unknown>): Promise<PairedDevice> {
    unavailable(this.reason);
  }

  async recordCommandResult(
    _connectorToken: string,
    _commandId: string,
    _payload: { status: "succeeded" | "failed"; result?: Record<string, unknown>; error?: string | null },
  ): Promise<CommandRecord> {
    unavailable(this.reason);
  }

  async resolveApproval(_userId: string, _approvalId: string): Promise<ApprovalRecord> {
    unavailable(this.reason);
  }

  describePersistence(): { backend: "blocked"; statePath: string; appBaseUrl: string; reason?: string | null } {
    return {
      backend: "blocked",
      statePath: "DATABASE_URL",
      appBaseUrl: APP_BASE_URL,
      reason: this.reason,
    };
  }
}

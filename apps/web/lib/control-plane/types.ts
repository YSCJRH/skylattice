export type CommandKind =
  | "task.run"
  | "task.resume"
  | "radar.scan"
  | "radar.schedule.run"
  | "radar.schedule.validate"
  | "radar.candidate.replay"
  | "radar.promotion.rollback"
  | "memory.search"
  | "memory.profile.propose"
  | "memory.review.confirm"
  | "memory.review.reject";

export type CommandStatus = "queued" | "claimed" | "succeeded" | "failed";

export type ControlPlaneBackend = "local-file" | "postgres" | "blocked";

export interface ControlPlaneStore {
  getDashboardSnapshot(userId: string): Promise<DashboardSnapshot>;
  listDevices(userId: string): Promise<PairedDevice[]>;
  listApprovals(userId: string): Promise<ApprovalRecord[]>;
  listCommands(userId: string): Promise<CommandRecord[]>;
  getCommand(userId: string, commandId: string): Promise<CommandRecord>;
  createPairingChallenge(userId: string): Promise<PairingChallenge>;
  claimPairing(pairingCode: string, deviceLabel: string, bridgeBaseUrl: string): Promise<PairedDevice>;
  revokeDevice(userId: string, deviceId: string): Promise<{ revoked: boolean; deviceId: string }>;
  queueCommand(userId: string, kind: CommandKind, payload: Record<string, unknown>, deviceId?: string | null): Promise<CommandRecord>;
  claimNextCommand(connectorToken: string): Promise<CommandRecord | null>;
  recordHeartbeat(connectorToken: string, payload: Record<string, unknown>): Promise<PairedDevice>;
  recordCommandResult(
    connectorToken: string,
    commandId: string,
    payload: { status: "succeeded" | "failed"; result?: Record<string, unknown>; error?: string | null },
  ): Promise<CommandRecord>;
  resolveApproval(userId: string, approvalId: string): Promise<ApprovalRecord>;
  describePersistence(): { backend: ControlPlaneBackend; statePath: string; appBaseUrl: string; reason?: string | null };
}

export interface PairedDevice {
  deviceId: string;
  userId: string;
  label: string;
  bridgeBaseUrl: string;
  connectorToken: string;
  lastSeenAt: string | null;
  online: boolean;
  latestKernelStatus: string | null;
  latestAuthSummary: string | null;
}

export type PublicPairedDevice = Omit<PairedDevice, "connectorToken">;

export interface PairingChallenge {
  pairingId: string;
  userId: string;
  pairingCode: string;
  createdAt: string;
  expiresAt: string;
  claimedAt: string | null;
  deviceId: string | null;
  deviceLabel: string | null;
  connectorToken: string | null;
}

export type PublicPairingChallenge = Omit<PairingChallenge, "connectorToken">;

export interface CommandRecord {
  commandId: string;
  userId: string;
  deviceId: string | null;
  kind: CommandKind;
  status: CommandStatus;
  createdAt: string;
  updatedAt: string;
  claimedAt: string | null;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
}

export interface ApprovalRecord {
  approvalId: string;
  userId: string;
  summary: string;
  requiredFlags: string[];
  status: "pending" | "resolved";
}

export interface DashboardSnapshot {
  backend: ControlPlaneBackend;
  userId: string;
  docsUrl: string;
  devices: PairedDevice[];
  pairings: PairingChallenge[];
  commands: CommandRecord[];
  pendingApprovals: ApprovalRecord[];
  memoryReviewCount: number;
}

export interface ControlPlaneState {
  devices: PairedDevice[];
  pairings: PairingChallenge[];
  commands: CommandRecord[];
  approvals: ApprovalRecord[];
}

import { randomUUID } from "node:crypto";

import { neon } from "@neondatabase/serverless";
import { and, desc, eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/neon-http";

import { APP_BASE_URL, DOCS_URL } from "@/lib/env";
import { approvalRecords, commandRequests, pairedDevices, pairingChallenges } from "@/lib/control-plane/schema";
import { newExpiry, nowIso, summarizeAuth } from "@/lib/control-plane/helpers";
import type {
  ApprovalRecord,
  CommandKind,
  CommandRecord,
  DashboardSnapshot,
  PairedDevice,
  PairingChallenge,
} from "@/lib/control-plane/types";

function databaseUrl(): string {
  const value = process.env.SKYLATTICE_CONTROL_PLANE_DATABASE_URL || process.env.DATABASE_URL;
  if (!value) {
    throw new Error("DATABASE_URL or SKYLATTICE_CONTROL_PLANE_DATABASE_URL is required for Postgres control-plane mode.");
  }
  return value;
}

function db() {
  return drizzle(neon(databaseUrl()), {
    schema: {
      approvalRecords,
      commandRequests,
      pairedDevices,
      pairingChallenges,
    },
  });
}

function toIso(value: Date | string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  if (value instanceof Date) {
    return value.toISOString();
  }
  return String(value);
}

function mapDevice(row: typeof pairedDevices.$inferSelect): PairedDevice {
  return {
    deviceId: row.deviceId,
    userId: row.userId,
    label: row.label,
    bridgeBaseUrl: row.bridgeBaseUrl,
    connectorToken: row.connectorToken,
    lastSeenAt: toIso(row.lastSeenAt),
    online: row.online,
    latestKernelStatus: row.latestKernelStatus,
    latestAuthSummary: row.latestAuthSummary,
  };
}

function mapPairing(row: typeof pairingChallenges.$inferSelect): PairingChallenge {
  return {
    pairingId: row.pairingId,
    userId: row.userId,
    pairingCode: row.pairingCode,
    createdAt: toIso(row.createdAt) || nowIso(),
    expiresAt: toIso(row.expiresAt) || nowIso(),
    claimedAt: toIso(row.claimedAt),
    deviceId: row.deviceId,
    deviceLabel: row.deviceLabel,
    connectorToken: row.connectorToken,
  };
}

function mapCommand(row: typeof commandRequests.$inferSelect): CommandRecord {
  return {
    commandId: row.commandId,
    userId: row.userId,
    deviceId: row.deviceId,
    kind: row.kind as CommandKind,
    status: row.status as CommandRecord["status"],
    createdAt: toIso(row.createdAt) || nowIso(),
    updatedAt: toIso(row.updatedAt) || nowIso(),
    claimedAt: toIso(row.claimedAt),
    payload: (row.payload ?? {}) as Record<string, unknown>,
    result: (row.result ?? null) as Record<string, unknown> | null,
    error: row.error,
  };
}

function mapApproval(row: typeof approvalRecords.$inferSelect): ApprovalRecord {
  return {
    approvalId: row.approvalId,
    userId: row.userId,
    summary: row.summary,
    requiredFlags: Array.isArray(row.requiredFlags) ? row.requiredFlags.map((item) => String(item)) : [],
    status: row.status as ApprovalRecord["status"],
  };
}

export class PostgresControlPlaneStore {
  async getDashboardSnapshot(userId: string): Promise<DashboardSnapshot> {
    const database = db();
    const [devices, pairings, commands, approvals] = await Promise.all([
      database.select().from(pairedDevices).where(eq(pairedDevices.userId, userId)),
      database.select().from(pairingChallenges).where(eq(pairingChallenges.userId, userId)),
      database
        .select()
        .from(commandRequests)
        .where(eq(commandRequests.userId, userId))
        .orderBy(desc(commandRequests.updatedAt))
        .limit(12),
      database
        .select()
        .from(approvalRecords)
        .where(and(eq(approvalRecords.userId, userId), eq(approvalRecords.status, "pending"))),
    ]);
    const mappedCommands = commands.map(mapCommand);
    return {
      backend: "postgres",
      userId,
      docsUrl: DOCS_URL,
      devices: devices.map(mapDevice),
      pairings: pairings.map(mapPairing),
      commands: mappedCommands,
      pendingApprovals: approvals.map(mapApproval),
      memoryReviewCount: mappedCommands.filter((command) => command.kind.startsWith("memory.") && command.status !== "failed").length,
    };
  }

  async listDevices(userId: string): Promise<PairedDevice[]> {
    const rows = await db().select().from(pairedDevices).where(eq(pairedDevices.userId, userId));
    return rows.map(mapDevice);
  }

  async listApprovals(userId: string): Promise<ApprovalRecord[]> {
    const rows = await db().select().from(approvalRecords).where(eq(approvalRecords.userId, userId));
    return rows.map(mapApproval);
  }

  async listCommands(userId: string): Promise<CommandRecord[]> {
    const rows = await db()
      .select()
      .from(commandRequests)
      .where(eq(commandRequests.userId, userId))
      .orderBy(desc(commandRequests.updatedAt));
    return rows.map(mapCommand);
  }

  async getCommand(userId: string, commandId: string): Promise<CommandRecord> {
    const [row] = await db()
      .select()
      .from(commandRequests)
      .where(and(eq(commandRequests.userId, userId), eq(commandRequests.commandId, commandId)))
      .limit(1);
    if (!row) {
      throw new Error("Command is unknown for the current user.");
    }
    return mapCommand(row);
  }

  async createPairingChallenge(userId: string): Promise<PairingChallenge> {
    const pairingId = randomUUID();
    const record = {
      pairingId,
      userId,
      pairingCode: randomUUID().replace(/-/g, "").slice(0, 8).toUpperCase(),
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + 15 * 60_000),
      claimedAt: null,
      deviceId: null,
      deviceLabel: null,
      connectorToken: null,
    };
    const [row] = await db().insert(pairingChallenges).values(record).returning();
    return mapPairing(row);
  }

  async claimPairing(pairingCode: string, deviceLabel: string, bridgeBaseUrl: string): Promise<PairedDevice> {
    const database = db();
    const [challenge] = await database
      .select()
      .from(pairingChallenges)
      .where(eq(pairingChallenges.pairingCode, pairingCode.trim().toUpperCase()))
      .limit(1);
    if (!challenge || challenge.claimedAt || new Date(challenge.expiresAt) <= new Date()) {
      throw new Error("Pairing code is unknown, expired, or already claimed.");
    }
    const deviceId = randomUUID();
    const connectorToken = randomUUID();
    const [device] = await database
      .insert(pairedDevices)
      .values({
        deviceId,
        userId: challenge.userId,
        label: deviceLabel.trim() || "Local Skylattice Agent",
        bridgeBaseUrl: bridgeBaseUrl.trim() || "http://127.0.0.1:8000",
        connectorToken,
        lastSeenAt: null,
        online: false,
        latestKernelStatus: null,
        latestAuthSummary: null,
      })
      .returning();
    await database
      .update(pairingChallenges)
      .set({
        claimedAt: new Date(),
        deviceId,
        deviceLabel: device.label,
        connectorToken,
      })
      .where(eq(pairingChallenges.pairingId, challenge.pairingId));
    return mapDevice(device);
  }

  async revokeDevice(userId: string, deviceId: string): Promise<{ revoked: boolean; deviceId: string }> {
    const database = db();
    const [device] = await database
      .select()
      .from(pairedDevices)
      .where(and(eq(pairedDevices.userId, userId), eq(pairedDevices.deviceId, deviceId)))
      .limit(1);
    if (!device) {
      throw new Error("Device is unknown for the current user.");
    }
    await database
      .update(commandRequests)
      .set({
        deviceId: null,
        updatedAt: new Date(),
      })
      .where(and(eq(commandRequests.deviceId, deviceId), eq(commandRequests.status, "queued")));
    await database.delete(pairedDevices).where(eq(pairedDevices.deviceId, deviceId));
    return { revoked: true, deviceId };
  }

  async queueCommand(userId: string, kind: CommandKind, payload: Record<string, unknown>, deviceId?: string | null): Promise<CommandRecord> {
    const database = db();
    let effectiveDeviceId = deviceId || null;
    if (!effectiveDeviceId) {
      const [fallbackDevice] = await database.select().from(pairedDevices).where(eq(pairedDevices.userId, userId)).limit(1);
      effectiveDeviceId = fallbackDevice?.deviceId || null;
    }
    const [row] = await database
      .insert(commandRequests)
      .values({
        commandId: randomUUID(),
        userId,
        deviceId: effectiveDeviceId,
        kind,
        status: "queued",
        createdAt: new Date(),
        updatedAt: new Date(),
        claimedAt: null,
        payload,
        result: null,
        error: null,
      })
      .returning();
    return mapCommand(row);
  }

  async claimNextCommand(connectorToken: string): Promise<CommandRecord | null> {
    const database = db();
    const [device] = await database.select().from(pairedDevices).where(eq(pairedDevices.connectorToken, connectorToken)).limit(1);
    if (!device) {
      throw new Error("Connector token is not paired to a device.");
    }
    const [command] = await database
      .select()
      .from(commandRequests)
      .where(and(eq(commandRequests.status, "queued"), eq(commandRequests.deviceId, device.deviceId)))
      .orderBy(desc(commandRequests.createdAt))
      .limit(1);
    if (!command) {
      return null;
    }
    const [updated] = await database
      .update(commandRequests)
      .set({
        status: "claimed",
        claimedAt: new Date(),
        updatedAt: new Date(),
      })
      .where(eq(commandRequests.commandId, command.commandId))
      .returning();
    return mapCommand(updated);
  }

  async recordHeartbeat(connectorToken: string, payload: Record<string, unknown>): Promise<PairedDevice> {
    const database = db();
    const [device] = await database.select().from(pairedDevices).where(eq(pairedDevices.connectorToken, connectorToken)).limit(1);
    if (!device) {
      throw new Error("Connector token is not paired to a device.");
    }
    const [updated] = await database
      .update(pairedDevices)
      .set({
        lastSeenAt: new Date(),
        online: true,
        latestKernelStatus: typeof payload.kernel === "object" && payload.kernel ? String((payload.kernel as Record<string, unknown>).status || "ok") : "ok",
        latestAuthSummary: summarizeAuth(payload),
      })
      .where(eq(pairedDevices.deviceId, device.deviceId))
      .returning();
    return mapDevice(updated);
  }

  async recordCommandResult(
    connectorToken: string,
    commandId: string,
    payload: { status: "succeeded" | "failed"; result?: Record<string, unknown>; error?: string | null },
  ): Promise<CommandRecord> {
    const database = db();
    const [device] = await database.select().from(pairedDevices).where(eq(pairedDevices.connectorToken, connectorToken)).limit(1);
    if (!device) {
      throw new Error("Connector token is not paired to a device.");
    }
    const [command] = await database
      .select()
      .from(commandRequests)
      .where(and(eq(commandRequests.commandId, commandId), eq(commandRequests.deviceId, device.deviceId)))
      .limit(1);
    if (!command) {
      throw new Error("Command is unknown for the current device.");
    }
    const [updated] = await database
      .update(commandRequests)
      .set({
        status: payload.status,
        result: payload.result || null,
        error: payload.error || null,
        updatedAt: new Date(),
      })
      .where(eq(commandRequests.commandId, command.commandId))
      .returning();
    await database
      .update(pairedDevices)
      .set({
        lastSeenAt: new Date(),
        online: true,
      })
      .where(eq(pairedDevices.deviceId, device.deviceId));
    if (payload.status === "failed") {
      const [existingApproval] = await database
        .select()
        .from(approvalRecords)
        .where(
          and(
            eq(approvalRecords.userId, updated.userId),
            eq(approvalRecords.summary, `Review failed ${updated.kind} command ${updated.commandId}`),
            eq(approvalRecords.status, "pending"),
          ),
        )
        .limit(1);
      if (!existingApproval) {
        await database.insert(approvalRecords).values({
          approvalId: randomUUID(),
          userId: updated.userId,
          summary: `Review failed ${updated.kind} command ${updated.commandId}`,
          requiredFlags: ["repo-write", "external-write"],
          status: "pending",
        });
      }
    }
    return mapCommand(updated);
  }

  async resolveApproval(userId: string, approvalId: string): Promise<ApprovalRecord> {
    const [row] = await db()
      .update(approvalRecords)
      .set({ status: "resolved" })
      .where(and(eq(approvalRecords.userId, userId), eq(approvalRecords.approvalId, approvalId)))
      .returning();
    if (!row) {
      throw new Error("Approval is unknown for the current user.");
    }
    return mapApproval(row);
  }

  describePersistence(): { backend: "postgres"; statePath: string; appBaseUrl: string } {
    return {
      backend: "postgres",
      statePath: "DATABASE_URL",
      appBaseUrl: APP_BASE_URL,
    };
  }
}

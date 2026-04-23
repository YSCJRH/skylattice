import { boolean, jsonb, pgTable, text, timestamp, uuid, varchar } from "drizzle-orm/pg-core";

export const controlPlaneUsers = pgTable("control_plane_users", {
  userId: text("user_id").primaryKey(),
  githubLogin: varchar("github_login", { length: 128 }).notNull(),
  email: varchar("email", { length: 320 }),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
});

export const pairedDevices = pgTable("paired_devices", {
  deviceId: uuid("device_id").primaryKey(),
  userId: text("user_id").notNull(),
  label: varchar("label", { length: 160 }).notNull(),
  bridgeBaseUrl: text("bridge_base_url").notNull(),
  connectorToken: text("connector_token").notNull(),
  lastSeenAt: timestamp("last_seen_at", { withTimezone: true }),
  online: boolean("online").notNull(),
  latestKernelStatus: varchar("latest_kernel_status", { length: 32 }),
  latestAuthSummary: text("latest_auth_summary"),
});

export const pairingChallenges = pgTable("pairing_challenges", {
  pairingId: uuid("pairing_id").primaryKey(),
  userId: text("user_id").notNull(),
  pairingCode: varchar("pairing_code", { length: 24 }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
  expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
  claimedAt: timestamp("claimed_at", { withTimezone: true }),
  deviceId: uuid("device_id"),
  deviceLabel: varchar("device_label", { length: 160 }),
  connectorToken: text("connector_token"),
});

export const commandRequests = pgTable("command_requests", {
  commandId: uuid("command_id").primaryKey(),
  userId: text("user_id").notNull(),
  deviceId: uuid("device_id"),
  kind: varchar("kind", { length: 64 }).notNull(),
  status: varchar("status", { length: 32 }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull(),
  claimedAt: timestamp("claimed_at", { withTimezone: true }),
  payload: jsonb("payload").notNull(),
  result: jsonb("result"),
  error: text("error"),
});

export const approvalRecords = pgTable("approval_records", {
  approvalId: uuid("approval_id").primaryKey(),
  userId: text("user_id").notNull(),
  summary: text("summary").notNull(),
  requiredFlags: jsonb("required_flags").notNull(),
  status: varchar("status", { length: 32 }).notNull(),
});

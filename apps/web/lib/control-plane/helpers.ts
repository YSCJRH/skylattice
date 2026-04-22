import { randomUUID } from "node:crypto";

import type { ApprovalRecord, ControlPlaneState } from "@/lib/control-plane/types";

export const DEFAULT_STATE: ControlPlaneState = {
  devices: [],
  pairings: [],
  commands: [],
  approvals: [],
};

export function nowIso(): string {
  return new Date().toISOString();
}

export function newExpiry(minutes: number): string {
  return new Date(Date.now() + minutes * 60_000).toISOString();
}

export function summarizeAuth(payload: Record<string, unknown>): string | null {
  const auth = payload.auth;
  if (!auth || typeof auth !== "object") {
    return null;
  }
  const issues = [
    !Boolean((auth as Record<string, unknown>).github_token_env_present) ? "missing GITHUB_TOKEN" : null,
    !Boolean((auth as Record<string, unknown>).gitlab_token_env_present) ? "missing GITLAB_TOKEN" : null,
    !Boolean((auth as Record<string, unknown>).openai_key_env_present) ? "missing OPENAI_API_KEY" : null,
  ].filter(Boolean);
  return issues.length ? issues.join(", ") : "All configured provider env vars present.";
}

export function upsertPendingApproval(
  approvals: ApprovalRecord[],
  userId: string,
  summary: string,
  requiredFlags: string[],
): ApprovalRecord[] {
  const existing = approvals.find((item) => item.userId === userId && item.summary === summary && item.status === "pending");
  if (existing) {
    return approvals;
  }
  return [
    {
      approvalId: randomUUID(),
      userId,
      summary,
      requiredFlags,
      status: "pending",
    },
    ...approvals,
  ];
}

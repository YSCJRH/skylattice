import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import type { CommandRecord, ControlPlaneStore, DashboardSnapshot } from "@/lib/control-plane/types";
import { DOCS_URL, hostedAlphaReadiness, isDemoPreviewEnabled } from "@/lib/env";

function emptySnapshot(userId: string): DashboardSnapshot {
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

export async function getControlPlanePageContext(): Promise<{
  userId: string;
  store: ControlPlaneStore;
  previewMode: boolean;
  persistence: ReturnType<ControlPlaneStore["describePersistence"]>;
  readiness: ReturnType<typeof hostedAlphaReadiness>;
  blocked: boolean;
  blockedReason: string | null;
  snapshot: DashboardSnapshot;
}> {
  const userId = await getSessionUserId();
  const previewMode = isDemoPreviewEnabled() && isGuestUserId(userId);
  const store = getControlPlaneStore();
  const persistence = store.describePersistence();
  const blocked = persistence.backend === "blocked";
  const snapshot = blocked ? emptySnapshot(userId) : await store.getDashboardSnapshot(userId);
  return {
    userId,
    store,
    previewMode,
    persistence,
    readiness: hostedAlphaReadiness(),
    blocked,
    blockedReason: persistence.reason || null,
    snapshot,
  };
}

export async function getControlPlaneCommandsForPage(
  context: Awaited<ReturnType<typeof getControlPlanePageContext>>,
): Promise<CommandRecord[]> {
  if (context.blocked) {
    return [];
  }
  return context.store.listCommands(context.userId);
}

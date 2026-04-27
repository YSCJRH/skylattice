import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { resolveControlPlaneMode, type ControlPlaneMode } from "@/lib/control-plane/mode";
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
  signedIn: boolean;
  mode: ControlPlaneMode;
  snapshot: DashboardSnapshot;
}> {
  const userId = await getSessionUserId();
  const signedIn = !isGuestUserId(userId);
  const previewMode = isDemoPreviewEnabled() && isGuestUserId(userId);
  const store = getControlPlaneStore();
  const persistence = store.describePersistence();
  const readiness = hostedAlphaReadiness();
  const blocked = persistence.backend === "blocked";
  const snapshot = blocked ? emptySnapshot(userId) : await store.getDashboardSnapshot(userId);
  const mode = resolveControlPlaneMode({
    previewMode,
    blocked,
    hostedAlpha: readiness.hostedAlpha,
    deviceCount: snapshot.devices.length,
  });
  return {
    userId,
    store,
    previewMode,
    persistence,
    readiness,
    blocked,
    blockedReason: persistence.reason || null,
    signedIn,
    mode,
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

import { NextRequest, NextResponse } from "next/server";

import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";
import type { CommandKind } from "@/lib/control-plane/types";

export async function GET() {
  const userId = await getSessionUserId();
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  const commands = await routed.store.listCommands(userId);
  return NextResponse.json({ commands });
}

export async function POST(request: NextRequest) {
  const userId = await getSessionUserId();
  if (isGuestUserId(userId)) {
    return NextResponse.json(
      {
        status: "blocked",
        error: "GitHub sign-in is required before queueing live commands.",
      },
      { status: 401 },
    );
  }
  const payload = (await request.json()) as {
    kind?: CommandKind;
    payload?: Record<string, unknown>;
    deviceId?: string | null;
  };
  if (!payload.kind) {
    return NextResponse.json({ status: "error", error: "Command kind is required." }, { status: 400 });
  }
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  const command = await routed.store.queueCommand(
    userId,
    payload.kind,
    payload.payload || {},
    payload.deviceId || null,
  );
  return NextResponse.json(command, { status: 201 });
}

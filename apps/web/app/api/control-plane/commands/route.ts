import { NextRequest, NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import type { CommandKind } from "@/lib/control-plane/types";

export async function GET() {
  const userId = await getSessionUserId();
  const commands = await getControlPlaneStore().listCommands(userId);
  return NextResponse.json({ commands });
}

export async function POST(request: NextRequest) {
  const userId = await getSessionUserId();
  if (userId === "guest@skylattice.local") {
    return NextResponse.json(
      {
        status: "blocked",
        error: "GitHub sign-in is required before queueing commands.",
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
  const command = await getControlPlaneStore().queueCommand(
    userId,
    payload.kind,
    payload.payload || {},
    payload.deviceId || null,
  );
  return NextResponse.json(command, { status: 201 });
}

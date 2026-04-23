import { NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";

export async function GET(
  _request: Request,
  context: { params: Promise<{ commandId: string }> },
) {
  const userId = await getSessionUserId();
  const { commandId } = await context.params;
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  try {
    const command = await routed.store.getCommand(userId, commandId);
    return NextResponse.json({ command });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load command.",
      },
      { status: 404 },
    );
  }
}

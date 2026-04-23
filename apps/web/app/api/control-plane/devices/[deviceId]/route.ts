import { NextResponse } from "next/server";

import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";

export async function DELETE(
  _request: Request,
  context: { params: Promise<{ deviceId: string }> },
) {
  const userId = await getSessionUserId();
  if (isGuestUserId(userId)) {
    return NextResponse.json(
      {
        status: "blocked",
        error: "GitHub sign-in is required before revoking live devices.",
      },
      { status: 401 },
    );
  }
  const { deviceId } = await context.params;
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  try {
    const result = await routed.store.revokeDevice(userId, deviceId);
    return NextResponse.json({ status: "ok", ...result });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        error: error instanceof Error ? error.message : "Unable to revoke device.",
      },
      { status: 400 },
    );
  }
}

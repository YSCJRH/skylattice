import { NextResponse } from "next/server";

import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";

export async function POST(
  _request: Request,
  context: { params: Promise<{ approvalId: string }> },
) {
  const userId = await getSessionUserId();
  if (isGuestUserId(userId)) {
    return NextResponse.json(
      {
        status: "blocked",
        error: "GitHub sign-in is required before resolving live approval reminders.",
      },
      { status: 401 },
    );
  }
  const { approvalId } = await context.params;
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  try {
    const approval = await routed.store.resolveApproval(userId, approvalId);
    return NextResponse.json({ status: "ok", approval });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        error: error instanceof Error ? error.message : "Unable to resolve approval.",
      },
      { status: 400 },
    );
  }
}

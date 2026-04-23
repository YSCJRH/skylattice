import { NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";

export async function GET() {
  const userId = await getSessionUserId();
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  const approvals = await routed.store.listApprovals(userId);
  return NextResponse.json({ approvals });
}

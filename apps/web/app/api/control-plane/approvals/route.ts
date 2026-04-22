import { NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";

export async function GET() {
  const userId = await getSessionUserId();
  const approvals = await getControlPlaneStore().listApprovals(userId);
  return NextResponse.json({ approvals });
}

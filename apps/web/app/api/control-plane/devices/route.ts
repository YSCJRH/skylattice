import { NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { toPublicDevices } from "@/lib/control-plane/public";
import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";

export async function GET() {
  const userId = await getSessionUserId();
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  const devices = toPublicDevices(await routed.store.listDevices(userId));
  return NextResponse.json({ devices });
}

import { NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";

export async function GET() {
  const userId = await getSessionUserId();
  const devices = await getControlPlaneStore().listDevices(userId);
  return NextResponse.json({ devices });
}

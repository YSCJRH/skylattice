import { NextRequest, NextResponse } from "next/server";

import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";

function connectorToken(request: NextRequest): string {
  return request.headers.get("x-skylattice-connector-token") || "";
}

export async function POST(request: NextRequest) {
  const token = connectorToken(request);
  if (!token) {
    return NextResponse.json({ status: "error", error: "Missing connector token." }, { status: 401 });
  }
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  try {
    const payload = (await request.json()) as Record<string, unknown>;
    const device = await routed.store.recordHeartbeat(token, payload);
    return NextResponse.json({ status: "ok", device });
  } catch (error) {
    return NextResponse.json(
      { status: "error", error: error instanceof Error ? error.message : "Heartbeat failed." },
      { status: 400 },
    );
  }
}

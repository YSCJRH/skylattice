import { NextRequest, NextResponse } from "next/server";

import { getControlPlaneStore } from "@/lib/control-plane/store";

function connectorToken(request: NextRequest): string {
  return request.headers.get("x-skylattice-connector-token") || "";
}

export async function POST(request: NextRequest) {
  const token = connectorToken(request);
  if (!token) {
    return NextResponse.json({ status: "error", error: "Missing connector token." }, { status: 401 });
  }
  try {
    const payload = (await request.json()) as Record<string, unknown>;
    const device = await getControlPlaneStore().recordHeartbeat(token, payload);
    return NextResponse.json({ status: "ok", device });
  } catch (error) {
    return NextResponse.json(
      { status: "error", error: error instanceof Error ? error.message : "Heartbeat failed." },
      { status: 400 },
    );
  }
}

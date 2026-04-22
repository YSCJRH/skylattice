import { NextRequest, NextResponse } from "next/server";

import { getControlPlaneStore } from "@/lib/control-plane/store";

function connectorToken(request: NextRequest): string {
  return request.headers.get("x-skylattice-connector-token") || "";
}

export async function GET(request: NextRequest) {
  const token = connectorToken(request);
  if (!token) {
    return NextResponse.json({ status: "error", error: "Missing connector token." }, { status: 401 });
  }
  try {
    const command = await getControlPlaneStore().claimNextCommand(token);
    return NextResponse.json({ status: "ok", command });
  } catch (error) {
    return NextResponse.json(
      { status: "error", error: error instanceof Error ? error.message : "Unable to claim command." },
      { status: 400 },
    );
  }
}

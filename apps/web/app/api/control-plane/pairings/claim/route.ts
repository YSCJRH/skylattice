import { NextRequest, NextResponse } from "next/server";

import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as {
    pairingCode?: string;
    deviceLabel?: string;
    bridgeBaseUrl?: string;
  };
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  try {
    const device = await routed.store.claimPairing(
      String(payload.pairingCode || ""),
      String(payload.deviceLabel || "Local Skylattice Agent"),
      String(payload.bridgeBaseUrl || "http://127.0.0.1:8000"),
    );
    return NextResponse.json(device, { status: 201 });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        error: error instanceof Error ? error.message : "Unable to claim pairing.",
      },
      { status: 400 },
    );
  }
}

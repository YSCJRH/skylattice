import { NextRequest, NextResponse } from "next/server";

import { getControlPlaneStore } from "@/lib/control-plane/store";

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as {
    pairingCode?: string;
    deviceLabel?: string;
    bridgeBaseUrl?: string;
  };
  try {
    const device = await getControlPlaneStore().claimPairing(
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

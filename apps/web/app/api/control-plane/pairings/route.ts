import { NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";

export async function GET() {
  const userId = await getSessionUserId();
  const snapshot = await getControlPlaneStore().getDashboardSnapshot(userId);
  return NextResponse.json({ pairings: snapshot.pairings, devices: snapshot.devices });
}

export async function POST() {
  const userId = await getSessionUserId();
  if (userId === "guest@skylattice.local") {
    return NextResponse.json(
      {
        status: "blocked",
        error: "GitHub sign-in is required before creating a pairing code.",
      },
      { status: 401 },
    );
  }
  const pairing = await getControlPlaneStore().createPairingChallenge(userId);
  return NextResponse.json(pairing, { status: 201 });
}

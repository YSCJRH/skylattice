import { NextResponse } from "next/server";

import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { toPublicDevices, toPublicPairings } from "@/lib/control-plane/public";
import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";

export async function GET() {
  const userId = await getSessionUserId();
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  const snapshot = await routed.store.getDashboardSnapshot(userId);
  return NextResponse.json({ pairings: toPublicPairings(snapshot.pairings), devices: toPublicDevices(snapshot.devices) });
}

export async function POST() {
  const userId = await getSessionUserId();
  if (isGuestUserId(userId)) {
    return NextResponse.json(
      {
        status: "blocked",
        error: "GitHub sign-in is required before creating a live pairing code.",
      },
      { status: 401 },
    );
  }
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  const pairing = await routed.store.createPairingChallenge(userId);
  return NextResponse.json(pairing, { status: 201 });
}

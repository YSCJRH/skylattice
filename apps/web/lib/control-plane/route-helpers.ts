import { NextResponse } from "next/server";

import { getControlPlaneStore } from "@/lib/control-plane/store";
import type { ControlPlaneStore } from "@/lib/control-plane/types";
import { hostedAlphaReadiness } from "@/lib/env";

export function blockedControlPlaneResponse(reason?: string | null) {
  const readiness = hostedAlphaReadiness();
  return NextResponse.json(
    {
      status: "blocked",
      error: reason || "Hosted Alpha configuration is incomplete for live control-plane requests.",
      blockers: readiness.blockers,
    },
    { status: 503 },
  );
}

export function getRoutableControlPlaneStore():
  | { store: ControlPlaneStore; response?: never }
  | { store?: never; response: NextResponse }
{
  const store = getControlPlaneStore();
  const persistence = store.describePersistence();
  if (persistence.backend === "blocked") {
    return { response: blockedControlPlaneResponse(persistence.reason) };
  }
  return { store };
}

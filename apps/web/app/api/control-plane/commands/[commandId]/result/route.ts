import { NextRequest, NextResponse } from "next/server";

import { getRoutableControlPlaneStore } from "@/lib/control-plane/route-helpers";

function connectorToken(request: NextRequest): string {
  return request.headers.get("x-skylattice-connector-token") || "";
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ commandId: string }> },
) {
  const token = connectorToken(request);
  if (!token) {
    return NextResponse.json({ status: "error", error: "Missing connector token." }, { status: 401 });
  }
  const { commandId } = await context.params;
  const payload = (await request.json()) as {
    status?: "succeeded" | "failed";
    result?: Record<string, unknown>;
    error?: string | null;
  };
  const routed = getRoutableControlPlaneStore();
  if ("response" in routed) {
    return routed.response;
  }
  try {
    const command = await routed.store.recordCommandResult(token, commandId, {
      status: payload.status || "succeeded",
      result: payload.result,
      error: payload.error,
    });
    return NextResponse.json({ status: "ok", command });
  } catch (error) {
    return NextResponse.json(
      { status: "error", error: error instanceof Error ? error.message : "Unable to record command result." },
      { status: 400 },
    );
  }
}

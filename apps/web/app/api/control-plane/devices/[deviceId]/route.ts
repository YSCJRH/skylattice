import { NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";

export async function DELETE(
  _request: Request,
  context: { params: Promise<{ deviceId: string }> },
) {
  const userId = await getSessionUserId();
  const { deviceId } = await context.params;
  try {
    const result = await getControlPlaneStore().revokeDevice(userId, deviceId);
    return NextResponse.json({ status: "ok", ...result });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        error: error instanceof Error ? error.message : "Unable to revoke device.",
      },
      { status: 400 },
    );
  }
}

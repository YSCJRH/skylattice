import { NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";

export async function GET(
  _request: Request,
  context: { params: Promise<{ commandId: string }> },
) {
  const userId = await getSessionUserId();
  const { commandId } = await context.params;
  try {
    const command = await getControlPlaneStore().getCommand(userId, commandId);
    return NextResponse.json({ command });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load command.",
      },
      { status: 404 },
    );
  }
}

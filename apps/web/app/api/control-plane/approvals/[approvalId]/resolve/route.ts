import { NextResponse } from "next/server";

import { getSessionUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";

export async function POST(
  _request: Request,
  context: { params: Promise<{ approvalId: string }> },
) {
  const userId = await getSessionUserId();
  const { approvalId } = await context.params;
  try {
    const approval = await getControlPlaneStore().resolveApproval(userId, approvalId);
    return NextResponse.json({ status: "ok", approval });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        error: error instanceof Error ? error.message : "Unable to resolve approval.",
      },
      { status: 400 },
    );
  }
}

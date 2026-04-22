import Link from "next/link";
import { notFound } from "next/navigation";

import { SectionHeading, StatusChip, StickerCard, WorkspaceHero } from "@/components/ui";
import { getSessionUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";

function tone(status: string) {
  if (status === "succeeded") {
    return "quaternary" as const;
  }
  if (status === "failed") {
    return "secondary" as const;
  }
  return "tertiary" as const;
}

export default async function CommandDetailPage({
  params,
}: {
  params: Promise<{ commandId: string }>;
}) {
  const userId = await getSessionUserId();
  const { commandId } = await params;

  const command = await getControlPlaneStore()
    .getCommand(userId, commandId)
    .catch(() => null);

  if (!command) {
    notFound();
  }

  return (
    <main className="space-y-8">
      <WorkspaceHero
        title={`Command ${command.commandId}`}
        description="A dedicated drill-down page for a single hosted control-plane command record."
        chips={
          <>
            <StatusChip tone={tone(command.status)}>{command.status}</StatusChip>
            <StatusChip tone="accent">{command.kind}</StatusChip>
          </>
        }
      />
      <SectionHeading
        eyebrow="Command detail"
        title="Payload, result, and routing context"
        description="Use this page when a workspace summary is not enough and you want the raw record that the hosted control plane is keeping for one operation."
        action={
          <Link
            href="/commands"
            className="rounded-full border-2 border-[var(--border)] bg-white px-4 py-2 text-sm font-bold shadow-[var(--shadow-hard)]"
          >
            Back to commands
          </Link>
        }
      />
      <div className="grid gap-6 xl:grid-cols-2">
        <StickerCard tone="white">
          <div className="space-y-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Payload</p>
            <pre className="overflow-auto rounded-[18px] border-2 border-[var(--border-soft)] bg-[var(--muted)] p-4 text-xs leading-6 text-[var(--foreground)]">
              {JSON.stringify(command.payload, null, 2)}
            </pre>
          </div>
        </StickerCard>
        <StickerCard tone="white">
          <div className="space-y-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Result</p>
            <pre className="overflow-auto rounded-[18px] border-2 border-[var(--border-soft)] bg-[var(--muted)] p-4 text-xs leading-6 text-[var(--foreground)]">
              {JSON.stringify(command.result, null, 2)}
            </pre>
          </div>
        </StickerCard>
      </div>
      <StickerCard tone="secondary">
        <div className="space-y-3 text-white">
          <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-white/80">Routing context</p>
          <p className="text-sm leading-7">created {command.createdAt}</p>
          <p className="text-sm leading-7">updated {command.updatedAt}</p>
          {command.claimedAt ? <p className="text-sm leading-7">claimed {command.claimedAt}</p> : null}
          {command.deviceId ? <p className="text-sm leading-7">device {command.deviceId}</p> : <p className="text-sm leading-7">no device locked yet</p>}
          {command.error ? <p className="text-sm leading-7">{command.error}</p> : null}
        </div>
      </StickerCard>
    </main>
  );
}

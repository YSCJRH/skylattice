import Link from "next/link";
import { notFound } from "next/navigation";

import { ButtonLink, SectionHeading, StatusChip, StickerCard, WorkspaceHero } from "@/components/ui";
import { getSessionUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import type { CommandRecord } from "@/lib/control-plane/types";

function tone(status: string) {
  if (status === "succeeded") {
    return "quaternary" as const;
  }
  if (status === "failed") {
    return "secondary" as const;
  }
  return "tertiary" as const;
}

function nextStep(command: CommandRecord): { title: string; description: string; href: string; label: string } {
  if (!command.deviceId) {
    return {
      title: "No local executor is locked yet.",
      description: "Pair a local agent or choose a target device before expecting this command to leave the hosted ledger.",
      href: "/connect",
      label: "Open pairing",
    };
  }
  if (command.status === "queued") {
    return {
      title: "Waiting for a connector claim.",
      description: "Run the local connector heartbeat or one-shot poll so the paired local runtime can claim this command.",
      href: "/connect",
      label: "Review connector path",
    };
  }
  if (command.status === "claimed") {
    return {
      title: "Local execution is in flight.",
      description: "The command has left the browser queue and is being handled by the paired local Skylattice runtime.",
      href: "/commands",
      label: "Back to command center",
    };
  }
  if (command.status === "failed") {
    return {
      title: "Review the failure before retrying.",
      description: "Failures often indicate missing credentials, local approval pressure, or runtime recovery steps. Inspect the error and resolve the local blocker rather than bypassing governance.",
      href: "/approvals",
      label: "Open approvals",
    };
  }
  return {
    title: "Command completed.",
    description: "Inspect the result payload here, then return to the command center or the originating workspace for follow-up work.",
    href: command.kind.startsWith("task.") ? "/tasks" : command.kind.startsWith("radar.") ? "/radar" : "/memory",
    label: "Open source workspace",
  };
}

function lifecycleSteps(command: CommandRecord): { label: string; detail: string; active: boolean }[] {
  return [
    {
      label: "Queued",
      detail: command.createdAt,
      active: true,
    },
    {
      label: "Claimed by local connector",
      detail: command.claimedAt || "Waiting for a paired connector",
      active: Boolean(command.claimedAt),
    },
    {
      label: command.status === "failed" ? "Failed with local pressure" : "Result recorded",
      detail: command.status === "queued" || command.status === "claimed" ? "Not finished yet" : command.updatedAt,
      active: command.status === "succeeded" || command.status === "failed",
    },
  ];
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
  const guidance = nextStep(command);
  const lifecycle = lifecycleSteps(command);

  return (
    <main className="space-y-8">
      <WorkspaceHero
        title={`Command ${command.commandId}`}
        description="A dedicated drill-down page for one hosted control-plane command record: lifecycle, routing, payload, result, error, and the safest next action."
        chips={
          <>
            <StatusChip tone={tone(command.status)}>{command.status}</StatusChip>
            <StatusChip tone="accent">{command.kind}</StatusChip>
            <StatusChip tone={command.deviceId ? "quaternary" : "secondary"}>
              {command.deviceId ? "target device set" : "no target device"}
            </StatusChip>
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
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <StickerCard tone="quaternary">
          <div className="space-y-4">
            <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Lifecycle</p>
            <div className="space-y-3">
              {lifecycle.map((step) => (
                <div key={step.label} className="rounded-[20px] border-2 border-[var(--border)] bg-white px-4 py-3 shadow-[var(--shadow-hard)]">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusChip tone={step.active ? "quaternary" : "tertiary"}>{step.active ? "active" : "waiting"}</StatusChip>
                    <span className="font-bold">{step.label}</span>
                  </div>
                  <p className="mt-2 text-sm leading-7 text-[var(--muted-foreground)]">{step.detail}</p>
                </div>
              ))}
            </div>
          </div>
        </StickerCard>
        <StickerCard tone={command.status === "failed" ? "secondary" : "white"}>
          <div className={command.status === "failed" ? "space-y-4 text-white" : "space-y-4"}>
            <p className={command.status === "failed" ? "text-xs font-extrabold uppercase tracking-[0.18em] text-white/80" : "text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]"}>Next safe action</p>
            <h2 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold">{guidance.title}</h2>
            <p className="text-sm leading-7">{guidance.description}</p>
            <ButtonLink href={guidance.href} variant="secondary">
              {guidance.label}
            </ButtonLink>
          </div>
        </StickerCard>
      </section>
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

import { CheckCircle2, Clock3, Cpu, Link2 } from "lucide-react";
import Link from "next/link";

import { ApprovalManager, DeviceReadinessPanel } from "@/components/control-plane-panels";
import { ButtonLink, HostedAlphaNotice, PreviewNotice, SectionHeading, StatusChip, StickerCard, WorkspaceHero } from "@/components/ui";
import { getControlPlanePageContext } from "@/lib/control-plane/page-context";
import { toPublicDevices } from "@/lib/control-plane/public";

export default async function DashboardPage() {
  const context = await getControlPlanePageContext();
  const { snapshot, previewMode, blocked, readiness } = context;
  const devices = toPublicDevices(snapshot.devices);

  return (
    <main className="space-y-8">
      {blocked ? (
        <HostedAlphaNotice
          description="This app is being treated like a Hosted Alpha deployment, so it will not fall back to the local-file control-plane store. Finish the deployment env before expecting live browser control."
          blockers={readiness.blockers}
          action={
            <ButtonLink href="/settings" variant="secondary">
              Review deployment settings
            </ButtonLink>
          }
        />
      ) : null}
      {previewMode ? (
        <PreviewNotice
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for Hosted Alpha
            </ButtonLink>
          }
        />
      ) : null}
      <WorkspaceHero
        title="Hosted control plane overview"
        description="This dashboard shows what the app can currently see: paired devices, recent command records, pending approvals, and whether your control-plane store is alive."
        chips={
          <>
            <StatusChip tone="accent">{snapshot.backend} store</StatusChip>
            <StatusChip tone={devices.length ? "quaternary" : "secondary"}>
              {devices.length ? `${devices.length} paired device(s)` : "No paired devices yet"}
            </StatusChip>
            <StatusChip tone="tertiary">{snapshot.commands.length} recent command(s)</StatusChip>
          </>
        }
      />
      <section className="grid gap-6 lg:grid-cols-3">
        <StickerCard tone="white" icon={<Cpu className="h-5 w-5" strokeWidth={2.5} />}>
          <div className="pt-7">
            <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-[var(--muted-foreground)]">Paired devices</p>
            <p className="mt-3 font-[family-name:var(--font-outfit)] text-4xl font-extrabold">{devices.length}</p>
            <p className="mt-3 text-sm leading-7 text-[var(--muted-foreground)]">The browser issues intent. Your paired local connector is the executor.</p>
            <div className="mt-4">
              <Link
                href="/devices"
                className="inline-flex rounded-full border-2 border-[var(--border)] bg-[var(--accent)] px-4 py-2 text-xs font-bold text-white shadow-[var(--shadow-hard)]"
              >
                Manage devices
              </Link>
            </div>
          </div>
        </StickerCard>
        <StickerCard tone="quaternary" icon={<Clock3 className="h-5 w-5" strokeWidth={2.5} />}>
          <div className="pt-7">
            <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-[var(--muted-foreground)]">Recent commands</p>
            <p className="mt-3 font-[family-name:var(--font-outfit)] text-4xl font-extrabold">{snapshot.commands.length}</p>
            <p className="mt-3 text-sm leading-7 text-[var(--muted-foreground)]">Task, radar, and memory intents queue here before a device claims them.</p>
          </div>
        </StickerCard>
        <StickerCard tone="secondary" icon={<CheckCircle2 className="h-5 w-5" strokeWidth={2.5} />}>
          <div className="pt-7">
            <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-white/80">Pending approvals</p>
            <p className="mt-3 font-[family-name:var(--font-outfit)] text-4xl font-extrabold text-white">{snapshot.pendingApprovals.length}</p>
            <p className="mt-3 text-sm leading-7 text-white">Failed or blocked commands can surface review needs without bypassing the local governance boundary.</p>
            <div className="mt-4">
              <Link
                href="/approvals"
                className="inline-flex rounded-full border-2 border-[var(--border)] bg-white px-4 py-2 text-xs font-bold text-[var(--foreground)] shadow-[var(--shadow-hard)]"
              >
                Open approvals
              </Link>
            </div>
          </div>
        </StickerCard>
        <StickerCard tone="tertiary" icon={<Clock3 className="h-5 w-5" strokeWidth={2.5} />}>
          <div className="pt-7">
            <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-[var(--muted-foreground)]">Memory activity</p>
            <p className="mt-3 font-[family-name:var(--font-outfit)] text-4xl font-extrabold">{snapshot.memoryReviewCount}</p>
            <p className="mt-3 text-sm leading-7 text-[var(--muted-foreground)]">Recent memory commands give the browser a quick read on review pressure and local knowledge work.</p>
          </div>
        </StickerCard>
      </section>
      <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <StickerCard tone="white" icon={<Link2 className="h-5 w-5" strokeWidth={2.5} />}>
          <div className="space-y-4 pt-7">
            <SectionHeading
              eyebrow="Next move"
              title="Pair a device before queueing commands."
              description="Without a paired local agent, the hosted control plane has nowhere truthful to send execution."
              action={<ButtonLink href="/connect">Open pairing</ButtonLink>}
            />
          </div>
        </StickerCard>
        <StickerCard tone="accent" className="px-8 py-8">
          <div className="space-y-4">
            <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-white/80">Latest command log</p>
            <div className="space-y-3">
              {snapshot.commands.length ? (
                snapshot.commands.map((command) => (
                  <div key={command.commandId} className="rounded-[20px] border-2 border-[var(--border)] bg-white px-4 py-3 text-sm text-[var(--foreground)] shadow-[var(--shadow-hard)]">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusChip tone={command.status === "succeeded" ? "quaternary" : command.status === "failed" ? "secondary" : "tertiary"}>
                        {command.status}
                      </StatusChip>
                      <span className="font-bold">{command.kind}</span>
                    </div>
                    <p className="mt-2 text-xs text-[var(--muted-foreground)]">{command.commandId}</p>
                    <div className="mt-3">
                      <Link
                        href={`/commands/${command.commandId}`}
                        className="inline-flex rounded-full border-2 border-[var(--border)] bg-[var(--accent)] px-4 py-2 text-xs font-bold text-white shadow-[var(--shadow-hard)]"
                      >
                        Inspect record
                      </Link>
                    </div>
                  </div>
                ))
              ) : (
                <div className="rounded-[20px] border-2 border-dashed border-[var(--border)] bg-white/20 px-4 py-4 text-sm text-white">
                  No commands yet. Sign in, pair a local device, and queue work from Tasks, Radar, or Memory.
                </div>
              )}
            </div>
            <div className="pt-2">
              <Link
                href="/commands"
                className="inline-flex rounded-full border-2 border-[var(--border)] bg-white px-4 py-2 text-sm font-bold text-[var(--foreground)] shadow-[var(--shadow-hard)]"
              >
                Open full command ledger
              </Link>
            </div>
          </div>
        </StickerCard>
      </section>
      <DeviceReadinessPanel devices={devices} />
      <ApprovalManager approvals={snapshot.pendingApprovals} previewMode={previewMode || blocked} />
    </main>
  );
}

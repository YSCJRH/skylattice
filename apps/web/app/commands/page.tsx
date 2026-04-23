import Link from "next/link";

import { ButtonLink, HostedAlphaNotice, PreviewNotice, SectionHeading, StatusChip, StickerCard, WorkspaceHero } from "@/components/ui";
import { getControlPlaneCommandsForPage, getControlPlanePageContext } from "@/lib/control-plane/page-context";
import type { CommandRecord } from "@/lib/control-plane/types";

type ScopeFilter = "all" | "task" | "radar" | "memory";
type StatusFilter = "all" | CommandRecord["status"];

function tone(status: string) {
  if (status === "succeeded") {
    return "quaternary" as const;
  }
  if (status === "failed") {
    return "secondary" as const;
  }
  return "tertiary" as const;
}

function matchesScope(command: CommandRecord, scope: ScopeFilter): boolean {
  if (scope === "all") {
    return true;
  }
  return command.kind.startsWith(`${scope}.`);
}

function matchesStatus(command: CommandRecord, status: StatusFilter): boolean {
  if (status === "all") {
    return true;
  }
  return command.status === status;
}

function filterHref(scope: ScopeFilter, status: StatusFilter): string {
  const params = new URLSearchParams();
  if (scope !== "all") {
    params.set("scope", scope);
  }
  if (status !== "all") {
    params.set("status", status);
  }
  const query = params.toString();
  return query ? `/commands?${query}` : "/commands";
}

function FilterPill({
  href,
  active,
  label,
}: {
  href: string;
  active: boolean;
  label: string;
}) {
  return (
    <Link
      href={href}
      className={[
        "rounded-full border-2 border-[var(--border)] px-4 py-2 text-xs font-bold uppercase tracking-[0.14em]",
        active ? "bg-[var(--accent)] text-white shadow-[var(--shadow-hard)]" : "bg-white text-[var(--foreground)]",
      ].join(" ")}
    >
      {label}
    </Link>
  );
}

export default async function CommandsPage({
  searchParams,
}: {
  searchParams: Promise<{ scope?: string; status?: string }>;
}) {
  const context = await getControlPlanePageContext();
  const { previewMode, blocked, readiness } = context;
  const commands = await getControlPlaneCommandsForPage(context);
  const params = await searchParams;
  const scope = (["all", "task", "radar", "memory"].includes(params.scope || "") ? params.scope : "all") as ScopeFilter;
  const status = (["all", "queued", "claimed", "succeeded", "failed"].includes(params.status || "") ? params.status : "all") as StatusFilter;
  const filtered = commands.filter((command) => matchesScope(command, scope) && matchesStatus(command, status));

  return (
    <main className="space-y-8">
      {blocked ? (
        <HostedAlphaNotice
          description="The command ledger becomes a real Hosted Alpha operating surface only after the live deployment is using public app auth and Postgres-backed control-plane state."
          blockers={readiness.blockers}
          action={
            <ButtonLink href="/settings" variant="secondary">
              Review hosted alpha blockers
            </ButtonLink>
          }
        />
      ) : null}
      {previewMode ? (
        <PreviewNotice
          title="Command ledger preview"
          description="These command records are representative preview data so first-time evaluators can inspect the control-plane shape before creating a live account or pairing a local device."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for Hosted Alpha commands
            </ButtonLink>
          }
        />
      ) : null}
      <WorkspaceHero
        title="Command ledger"
        description="A dedicated drill-down surface for every control-plane command record, regardless of whether it came from tasks, radar, memory, or onboarding."
        chips={
          <>
            <StatusChip tone="accent">{filtered.length} visible command(s)</StatusChip>
            <StatusChip tone="secondary">payloads</StatusChip>
            <StatusChip tone="tertiary">results</StatusChip>
          </>
        }
      />
      <SectionHeading
        eyebrow="Control plane"
        title="Browse command records as a first-class surface."
        description="Use scope and status filters to narrow the control-plane ledger down to the exact task, radar, or memory slice you want to inspect."
      />
      <StickerCard tone="white">
        <div className="space-y-5">
          <div className="space-y-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Scope</p>
            <div className="flex flex-wrap gap-2">
              {(["all", "task", "radar", "memory"] as ScopeFilter[]).map((item) => (
                <FilterPill
                  key={item}
                  href={filterHref(item, status)}
                  active={scope === item}
                  label={item}
                />
              ))}
            </div>
          </div>
          <div className="space-y-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Status</p>
            <div className="flex flex-wrap gap-2">
              {(["all", "queued", "claimed", "succeeded", "failed"] as StatusFilter[]).map((item) => (
                <FilterPill
                  key={item}
                  href={filterHref(scope, item)}
                  active={status === item}
                  label={item}
                />
              ))}
            </div>
          </div>
        </div>
      </StickerCard>
      <div className="space-y-4">
        {filtered.length ? (
          filtered.map((command) => (
            <StickerCard key={command.commandId} tone="white">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusChip tone={tone(command.status)}>{command.status}</StatusChip>
                  <span className="font-bold">{command.kind}</span>
                </div>
                <p className="text-sm leading-7 text-[var(--muted-foreground)]">
                  updated {command.updatedAt}
                  {command.deviceId ? ` - device ${command.deviceId}` : ""}
                </p>
                <Link
                  href={`/commands/${command.commandId}`}
                  className="inline-flex rounded-full border-2 border-[var(--border)] bg-[var(--accent)] px-4 py-2 text-sm font-bold text-white shadow-[var(--shadow-hard)]"
                >
                  Open command detail
                </Link>
              </div>
            </StickerCard>
          ))
        ) : (
          <StickerCard tone="white">
            <p className="text-sm leading-7 text-[var(--muted-foreground)]">
              No command records match the current filters. Try another scope or status, or queue new work from Tasks, Radar, Memory, or Connect.
            </p>
          </StickerCard>
        )}
      </div>
    </main>
  );
}

import { RadarCommandPanel } from "@/components/control-plane-panels";
import { CommandHistoryPanel } from "@/components/command-history";
import { ButtonLink, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import { isDemoPreviewEnabled } from "@/lib/env";

export default async function RadarPage() {
  const userId = await getSessionUserId();
  const snapshot = await getControlPlaneStore().getDashboardSnapshot(userId);
  const radarCommands = snapshot.commands.filter((command) => command.kind.startsWith("radar."));
  const previewMode = isDemoPreviewEnabled() && isGuestUserId(userId);

  return (
    <main className="space-y-8">
      {previewMode ? (
        <PreviewNotice
          title="Radar workspace preview"
          description="The preview keeps radar scans, schedule validation, and rollback surfaces visible without pretending the browser can drive live promotion before a real local runtime is connected."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for live radar control
            </ButtonLink>
          }
        />
      ) : null}
      <WorkspaceHero
        title="Technology radar workspace"
        description="Run scans, validate scheduled runs, replay candidates, and roll back promotions from the browser while the local runtime keeps the branch, ledger, and policy truth."
        chips={
          <>
            <StatusChip tone="accent">scan</StatusChip>
            <StatusChip tone="secondary">schedule</StatusChip>
            <StatusChip tone="tertiary">validate</StatusChip>
            <StatusChip tone="quaternary">rollback</StatusChip>
          </>
        }
      />
      <SectionHeading
        eyebrow="Radar control"
        title="Browser intent, local experiment execution."
        description="The hosted app can queue radar work without turning GitHub or the control plane into runtime truth."
      />
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <RadarCommandPanel devices={snapshot.devices} previewMode={previewMode} />
        <CommandHistoryPanel
          title="Latest radar outcomes"
          description="Scans, validations, replays, and rollbacks leave a visible command trail in the app even though the real work happens on the local agent."
          commands={radarCommands}
          emptyText="No radar commands yet. Queue a scan or schedule validation to populate this view."
          ledgerHref="/commands?scope=radar"
        />
      </div>
    </main>
  );
}

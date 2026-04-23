import { RadarCommandPanel } from "@/components/control-plane-panels";
import { CommandHistoryPanel } from "@/components/command-history";
import { ButtonLink, HostedAlphaNotice, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { getControlPlanePageContext } from "@/lib/control-plane/page-context";
import { toPublicDevices } from "@/lib/control-plane/public";

export default async function RadarPage() {
  const context = await getControlPlanePageContext();
  const { snapshot, previewMode, blocked, readiness } = context;
  const radarCommands = snapshot.commands.filter((command) => command.kind.startsWith("radar."));
  const devices = toPublicDevices(snapshot.devices);

  return (
    <main className="space-y-8">
      {blocked ? (
        <HostedAlphaNotice
          description="The radar workspace can only become a real Hosted Alpha surface after the deployment is using public app auth and Postgres-backed control-plane state."
          blockers={readiness.blockers}
          action={
            <ButtonLink href="/settings" variant="secondary">
              Review deployment blockers
            </ButtonLink>
          }
        />
      ) : null}
      {previewMode ? (
        <PreviewNotice
          title="Radar workspace preview"
          description="The preview keeps radar scans, schedule validation, and rollback surfaces visible without pretending the browser can drive live promotion before a real local runtime is connected."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for Hosted Alpha radar control
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
        <RadarCommandPanel devices={devices} previewMode={previewMode || blocked} />
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

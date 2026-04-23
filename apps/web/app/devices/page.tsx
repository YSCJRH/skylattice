import { DeviceManager, DeviceReadinessPanel } from "@/components/control-plane-panels";
import { ButtonLink, HostedAlphaNotice, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { getControlPlanePageContext } from "@/lib/control-plane/page-context";
import { toPublicDevices } from "@/lib/control-plane/public";

export default async function DevicesPage() {
  const context = await getControlPlanePageContext();
  const { snapshot, previewMode, blocked, readiness } = context;
  const devices = toPublicDevices(snapshot.devices);

  return (
    <main className="space-y-8">
      {blocked ? (
        <HostedAlphaNotice
          description="Device lifecycle management is part of the Hosted Alpha surface, but it should stay blocked until the deployment is using real auth and Postgres-backed control-plane state."
          blockers={readiness.blockers}
          action={
            <ButtonLink href="/settings" variant="secondary">
              Open deployment settings
            </ButtonLink>
          }
        />
      ) : null}
      {previewMode ? (
        <PreviewNotice
          title="Device management preview"
          description="The preview exposes representative paired-device and readiness cards so the browser-side trust model is visible before a live connector is attached."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for Hosted Alpha device control
            </ButtonLink>
          }
        />
      ) : null}
      <WorkspaceHero
        title="Devices"
        description="Manage paired local Skylattice agents, inspect their latest readiness heartbeat, and revoke connector trust when a machine should stop receiving commands."
        chips={
          <>
            <StatusChip tone="accent">{devices.length} device(s)</StatusChip>
            <StatusChip tone="secondary">revoke</StatusChip>
            <StatusChip tone="tertiary">readiness</StatusChip>
          </>
        }
      />
      <SectionHeading
        eyebrow="Control plane"
        title="Paired local agents as a first-class surface."
        description="This page separates long-lived device management from onboarding and dashboard summaries so operator trust stays explicit and reviewable."
      />
      <DeviceReadinessPanel devices={devices} />
      <DeviceManager devices={devices} previewMode={previewMode || blocked} />
    </main>
  );
}

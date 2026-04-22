import { DeviceManager, DeviceReadinessPanel } from "@/components/control-plane-panels";
import { ButtonLink, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import { isDemoPreviewEnabled } from "@/lib/env";

export default async function DevicesPage() {
  const userId = await getSessionUserId();
  const devices = await getControlPlaneStore().listDevices(userId);
  const previewMode = isDemoPreviewEnabled() && isGuestUserId(userId);

  return (
    <main className="space-y-8">
      {previewMode ? (
        <PreviewNotice
          title="Device management preview"
          description="The preview exposes representative paired-device and readiness cards so the browser-side trust model is visible before a live connector is attached."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for live device control
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
      <DeviceManager devices={devices} previewMode={previewMode} />
    </main>
  );
}

import { DeviceManager, DeviceReadinessPanel } from "@/components/control-plane-panels";
import { SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { getAppSession } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";

export default async function DevicesPage() {
  const session = await getAppSession();
  const userId = session?.user?.email || session?.user?.name || "guest@skylattice.local";
  const devices = await getControlPlaneStore().listDevices(userId);

  return (
    <main className="space-y-8">
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
      <DeviceManager devices={devices} />
    </main>
  );
}

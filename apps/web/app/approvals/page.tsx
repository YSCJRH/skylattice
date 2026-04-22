import { ApprovalManager } from "@/components/control-plane-panels";
import { SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { getAppSession } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";

export default async function ApprovalsPage() {
  const session = await getAppSession();
  const userId = session?.user?.email || session?.user?.name || "guest@skylattice.local";
  const approvals = await getControlPlaneStore().listApprovals(userId);
  const pending = approvals.filter((item) => item.status === "pending");

  return (
    <main className="space-y-8">
      <WorkspaceHero
        title="Approvals"
        description="Review the hosted control-plane reminders that point back to local governance pressure. These reminders help visibility; they do not bypass runtime approval rules."
        chips={
          <>
            <StatusChip tone="accent">{pending.length} pending</StatusChip>
            <StatusChip tone="secondary">resolve reminders</StatusChip>
            <StatusChip tone="tertiary">{approvals.length} total</StatusChip>
          </>
        }
      />
      <SectionHeading
        eyebrow="Governance visibility"
        title="Approval reminders deserve their own page."
        description="Use this surface when you need to review blocked or failed command pressure without mixing it into task, radar, or memory workspaces."
      />
      <ApprovalManager approvals={pending} />
    </main>
  );
}

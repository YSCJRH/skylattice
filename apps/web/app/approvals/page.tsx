import { ApprovalManager } from "@/components/control-plane-panels";
import { ButtonLink, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import { isDemoPreviewEnabled } from "@/lib/env";

export default async function ApprovalsPage() {
  const userId = await getSessionUserId();
  const approvals = await getControlPlaneStore().listApprovals(userId);
  const pending = approvals.filter((item) => item.status === "pending");
  const previewMode = isDemoPreviewEnabled() && isGuestUserId(userId);

  return (
    <main className="space-y-8">
      {previewMode ? (
        <PreviewNotice
          title="Approval visibility preview"
          description="The preview keeps governance reminders visible without pretending a guest session can resolve live approval pressure from a real local runtime."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for live approvals
            </ButtonLink>
          }
        />
      ) : null}
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
      <ApprovalManager approvals={pending} previewMode={previewMode} />
    </main>
  );
}

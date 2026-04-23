import { ApprovalManager } from "@/components/control-plane-panels";
import { ButtonLink, HostedAlphaNotice, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { getControlPlanePageContext } from "@/lib/control-plane/page-context";

export default async function ApprovalsPage() {
  const context = await getControlPlanePageContext();
  const { snapshot, previewMode, blocked, readiness } = context;
  const approvals = snapshot.pendingApprovals;
  const pending = approvals.filter((item) => item.status === "pending");

  return (
    <main className="space-y-8">
      {blocked ? (
        <HostedAlphaNotice
          description="Approval visibility is part of the live operating surface, but a Hosted Alpha deployment must be fully configured before this page should handle real reminders."
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
          title="Approval visibility preview"
          description="The preview keeps governance reminders visible without pretending a guest session can resolve live approval pressure from a real local runtime."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for Hosted Alpha approvals
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
      <ApprovalManager approvals={pending} previewMode={previewMode || blocked} />
    </main>
  );
}

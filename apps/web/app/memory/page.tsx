import { MemoryCommandPanel } from "@/components/control-plane-panels";
import { CommandHistoryPanel } from "@/components/command-history";
import { ButtonLink, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import { isDemoPreviewEnabled } from "@/lib/env";

export default async function MemoryPage() {
  const userId = await getSessionUserId();
  const snapshot = await getControlPlaneStore().getDashboardSnapshot(userId);
  const memoryCommands = snapshot.commands.filter((command) => command.kind.startsWith("memory."));
  const previewMode = isDemoPreviewEnabled() && isGuestUserId(userId);

  return (
    <main className="space-y-8">
      {previewMode ? (
        <PreviewNotice
          title="Memory workspace preview"
          description="This preview exposes representative search, proposal, and review records so the browser-side memory workflow is legible before you connect a live local memory store."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for live memory actions
            </ButtonLink>
          }
        />
      ) : null}
      <WorkspaceHero
        title="Memory workspace"
        description="Search local memory, propose profile updates, and resolve review items from the browser while private memory content still stays local by default."
        chips={
          <>
            <StatusChip tone="accent">search</StatusChip>
            <StatusChip tone="secondary">review</StatusChip>
            <StatusChip tone="tertiary">profile</StatusChip>
          </>
        }
      />
      <SectionHeading
        eyebrow="Memory control"
        title="Review-driven memory actions remain review-driven."
        description="The app can request memory actions, but it does not dissolve the local review boundary that already governs profile, semantic, and procedural changes."
      />
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <MemoryCommandPanel devices={snapshot.devices} previewMode={previewMode} />
        <CommandHistoryPanel
          title="Latest memory results"
          description="Searches, proposals, confirms, and rejects stay visible here so the browser feels like a real workspace instead of a one-shot form."
          commands={memoryCommands}
          emptyText="No memory commands yet. Queue a memory search or profile proposal to populate this panel."
          ledgerHref="/commands?scope=memory"
        />
      </div>
    </main>
  );
}

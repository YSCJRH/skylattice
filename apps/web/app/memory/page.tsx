import { MemoryCommandPanel } from "@/components/control-plane-panels";
import { CommandHistoryPanel } from "@/components/command-history";
import { ButtonLink, HostedAlphaNotice, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { commandComposerGate } from "@/lib/control-plane/mode";
import { getControlPlanePageContext } from "@/lib/control-plane/page-context";
import { toPublicDevices } from "@/lib/control-plane/public";

export default async function MemoryPage() {
  const context = await getControlPlanePageContext();
  const { snapshot, previewMode, blocked, readiness } = context;
  const memoryCommands = snapshot.commands.filter((command) => command.kind.startsWith("memory."));
  const devices = toPublicDevices(snapshot.devices);
  const gate = commandComposerGate(context.mode, devices.length, context.signedIn);

  return (
    <main className="space-y-8">
      {blocked ? (
        <HostedAlphaNotice
          description="The memory workspace can render, but live browser-triggered memory actions need the Hosted Alpha deployment to be fully configured first."
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
          title="Memory workspace preview"
          description="This preview exposes representative search, proposal, and review records so the browser-side memory workflow is legible before you connect a live local memory store."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for Hosted Alpha memory actions
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
        description="The app can request memory actions after pairing, but it does not dissolve the local review boundary that already governs profile, semantic, and procedural changes."
        action={
          gate.disabled ? (
            <ButtonLink href={gate.actionHref || "/connect"} variant="secondary">
              {gate.actionLabel || "Pair a local agent"}
            </ButtonLink>
          ) : (
            <ButtonLink href="/commands?scope=memory" variant="secondary">
              Open memory commands
            </ButtonLink>
          )
        }
      />
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <MemoryCommandPanel devices={devices} previewMode={previewMode || blocked} gate={gate} />
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

import { CommandHistoryPanel } from "@/components/command-history";
import { ButtonLink, HostedAlphaNotice, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { TaskCommandComposer } from "@/components/control-plane-panels";
import { getControlPlanePageContext } from "@/lib/control-plane/page-context";
import { toPublicDevices } from "@/lib/control-plane/public";

export default async function TasksPage() {
  const context = await getControlPlanePageContext();
  const { snapshot, previewMode, blocked, readiness } = context;
  const taskCommands = snapshot.commands.filter((command) => command.kind.startsWith("task."));
  const devices = toPublicDevices(snapshot.devices);

  return (
    <main className="space-y-8">
      {blocked ? (
        <HostedAlphaNotice
          description="The task workspace is ready in the UI, but live browser-triggered task runs stay blocked until the Hosted Alpha deployment has real auth and control-plane persistence."
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
          title="Task workspace preview"
          description="These task records are representative preview data. Sign in and pair a local agent when you want to queue a real governed task run from the browser."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for Hosted Alpha tasks
            </ButtonLink>
          }
        />
      ) : null}
      <WorkspaceHero
        title="Task workspace"
        description="Queue task runs from the browser, inspect what the hosted control plane knows, and keep the real planning and edit execution on the paired local runtime."
        chips={
          <>
            <StatusChip tone="accent">run</StatusChip>
            <StatusChip tone="secondary">resume</StatusChip>
            <StatusChip tone="tertiary">inspect</StatusChip>
          </>
        }
      />
      <SectionHeading
        eyebrow="Command intent"
        title="Create governed work, not blind automation."
        description="The form below writes command intent into the hosted control plane. Your paired connector claims it and executes through the same local runtime service used by the CLI."
      />
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <TaskCommandComposer devices={devices} previewMode={previewMode || blocked} />
        <CommandHistoryPanel
          title="Latest task command results"
          description="Recent task commands stay visible here so the workspace is useful after queueing work, not only before it."
          commands={taskCommands}
          emptyText="No task commands yet. Queue a governed run to start seeing local runtime outcomes here."
          ledgerHref="/commands?scope=task"
        />
      </div>
    </main>
  );
}

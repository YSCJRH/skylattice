import { CommandHistoryPanel } from "@/components/command-history";
import { ButtonLink, PreviewNotice, SectionHeading, StatusChip, WorkspaceHero } from "@/components/ui";
import { TaskCommandComposer } from "@/components/control-plane-panels";
import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import { isDemoPreviewEnabled } from "@/lib/env";

export default async function TasksPage() {
  const userId = await getSessionUserId();
  const snapshot = await getControlPlaneStore().getDashboardSnapshot(userId);
  const taskCommands = snapshot.commands.filter((command) => command.kind.startsWith("task."));
  const previewMode = isDemoPreviewEnabled() && isGuestUserId(userId);

  return (
    <main className="space-y-8">
      {previewMode ? (
        <PreviewNotice
          title="Task workspace preview"
          description="These task records are representative preview data. Sign in and pair a local agent when you want to queue a real governed task run from the browser."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for live tasks
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
        <TaskCommandComposer devices={snapshot.devices} previewMode={previewMode} />
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

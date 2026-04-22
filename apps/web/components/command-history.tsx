import Link from "next/link";
import { AlertCircle, CheckCircle2, Clock3, FileClock, Radar, Search, ShieldCheck } from "lucide-react";

import { StatusChip, StickerCard } from "@/components/ui";
import type { CommandRecord } from "@/lib/control-plane/types";

function commandIcon(kind: string) {
  if (kind.startsWith("task.")) {
    return <ShieldCheck className="h-5 w-5" strokeWidth={2.5} />;
  }
  if (kind.startsWith("radar.")) {
    return <Radar className="h-5 w-5" strokeWidth={2.5} />;
  }
  return <Search className="h-5 w-5" strokeWidth={2.5} />;
}

function commandTone(status: CommandRecord["status"]) {
  if (status === "succeeded") {
    return "quaternary" as const;
  }
  if (status === "failed") {
    return "secondary" as const;
  }
  return "tertiary" as const;
}

function summarizeResult(command: CommandRecord): string {
  const result = command.result || {};
  if (command.kind === "task.run" || command.kind === "task.resume") {
    const run = result.run;
    if (run && typeof run === "object") {
      const runId = String((run as Record<string, unknown>).run_id || "");
      const status = String((run as Record<string, unknown>).status || "");
      return `Run ${runId || "created"} ${status || "updated"}.`;
    }
  }
  if (command.kind === "radar.scan" || command.kind === "radar.schedule.run" || command.kind === "radar.candidate.replay") {
    const run = result.run;
    if (run && typeof run === "object") {
      const runId = String((run as Record<string, unknown>).run_id || "");
      return `Radar run ${runId || "created"} recorded.`;
    }
  }
  if (command.kind === "radar.schedule.validate") {
    const valid = typeof result.valid === "boolean" ? result.valid : null;
    const outputPath = typeof result.output_path === "string" ? result.output_path : null;
    return valid === null
      ? "Schedule validation completed."
      : `Schedule validation ${valid ? "passed" : "failed"}${outputPath ? ` at ${outputPath}` : ""}.`;
  }
  if (command.kind === "radar.promotion.rollback") {
    const promotionId = typeof result.promotion_id === "string" ? result.promotion_id : null;
    return promotionId ? `Rollback recorded for promotion ${promotionId}.` : "Rollback completed.";
  }
  if (command.kind === "memory.search") {
    const records = Array.isArray(result.records) ? result.records.length : 0;
    return `Memory search returned ${records} record(s).`;
  }
  if (command.kind === "memory.profile.propose") {
    const recordId = typeof result.record_id === "string" ? result.record_id : null;
    return recordId ? `Profile proposal created as ${recordId}.` : "Profile proposal created.";
  }
  if (command.kind === "memory.review.confirm" || command.kind === "memory.review.reject") {
    const status = typeof result.status === "string" ? result.status : null;
    const recordId = typeof result.record_id === "string" ? result.record_id : null;
    return `${command.kind.endsWith("confirm") ? "Confirm" : "Reject"} completed${recordId ? ` for ${recordId}` : ""}${status ? ` with status ${status}` : ""}.`;
  }
  return command.status === "failed" ? "Command failed." : "Command completed.";
}

function statusIcon(status: CommandRecord["status"]) {
  if (status === "succeeded") {
    return <CheckCircle2 className="h-4 w-4" strokeWidth={2.5} />;
  }
  if (status === "failed") {
    return <AlertCircle className="h-4 w-4" strokeWidth={2.5} />;
  }
  if (status === "claimed") {
    return <Clock3 className="h-4 w-4" strokeWidth={2.5} />;
  }
  return <FileClock className="h-4 w-4" strokeWidth={2.5} />;
}

function prettyJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2);
}

export function CommandHistoryPanel({
  title,
  description,
  commands,
  emptyText,
  ledgerHref,
  ledgerLabel = "Open filtered command ledger",
}: {
  title: string;
  description: string;
  commands: CommandRecord[];
  emptyText: string;
  ledgerHref?: string;
  ledgerLabel?: string;
}) {
  return (
    <StickerCard tone="white" icon={commandIcon(commands[0]?.kind || "task.run")}>
      <div className="space-y-4 pt-7">
        <div>
          <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-[var(--muted-foreground)]">Recent outcomes</p>
          <h3 className="mt-2 font-[family-name:var(--font-outfit)] text-2xl font-extrabold">{title}</h3>
          <p className="mt-2 text-sm leading-7 text-[var(--muted-foreground)]">{description}</p>
          {ledgerHref ? (
            <div className="mt-4">
              <Link
                href={ledgerHref}
                className="inline-flex rounded-full border-2 border-[var(--border)] bg-[var(--accent)] px-4 py-2 text-xs font-bold text-white shadow-[var(--shadow-hard)]"
              >
                {ledgerLabel}
              </Link>
            </div>
          ) : null}
        </div>
        <div className="space-y-3">
          {commands.length ? (
            commands.map((command) => (
              <div key={command.commandId} className="rounded-[20px] border-2 border-[var(--border)] bg-[var(--muted)] px-4 py-4">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusChip tone={commandTone(command.status)}>{command.status}</StatusChip>
                  <span className="inline-flex items-center gap-2 text-sm font-bold">
                    {statusIcon(command.status)}
                    {command.kind}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-7 text-[var(--foreground)]">{summarizeResult(command)}</p>
                {command.error ? (
                  <p className="mt-3 text-sm leading-7 text-[color:#be123c]">{command.error}</p>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-3 text-xs text-[var(--muted-foreground)]">
                  <span>{command.commandId}</span>
                  <span>{command.updatedAt}</span>
                  {command.deviceId ? <span>device {command.deviceId}</span> : null}
                </div>
                <div className="mt-4">
                  <Link
                    href={`/commands/${command.commandId}`}
                    className="inline-flex rounded-full border-2 border-[var(--border)] bg-[var(--accent)] px-4 py-2 text-xs font-bold text-white shadow-[var(--shadow-hard)]"
                  >
                    Open command page
                  </Link>
                </div>
                <details className="mt-4 rounded-[18px] border-2 border-[var(--border)] bg-white px-4 py-3">
                  <summary className="cursor-pointer text-sm font-bold">Inspect payload and result</summary>
                  <div className="mt-3 grid gap-3 xl:grid-cols-2">
                    <div className="space-y-2">
                      <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Payload</p>
                      <pre className="overflow-auto rounded-[14px] border-2 border-[var(--border-soft)] bg-[var(--muted)] p-3 text-[11px] leading-6 text-[var(--foreground)]">
                        {prettyJson(command.payload)}
                      </pre>
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Result</p>
                      <pre className="overflow-auto rounded-[14px] border-2 border-[var(--border-soft)] bg-[var(--muted)] p-3 text-[11px] leading-6 text-[var(--foreground)]">
                        {prettyJson(command.result)}
                      </pre>
                    </div>
                  </div>
                </details>
              </div>
            ))
          ) : (
            <div className="rounded-[20px] border-2 border-dashed border-[var(--border)] bg-white px-4 py-4 text-sm text-[var(--muted-foreground)]">
              {emptyText}
            </div>
          )}
        </div>
      </div>
    </StickerCard>
  );
}

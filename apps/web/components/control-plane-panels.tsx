"use client";

import { useMemo, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Tabs from "@radix-ui/react-tabs";
import { AlertCircle, CheckCircle2, Link2, LoaderCircle, Radar, ShieldCheck, Sparkles, Trash2 } from "lucide-react";

import { CandyButton, StatusChip, StickerCard } from "@/components/ui";
import type { ApprovalRecord, PairedDevice, PairingChallenge } from "@/lib/control-plane/types";
import { APP_BASE_URL } from "@/lib/env";

type Receipt = Record<string, unknown> | null;

async function submitJson(path: string, body?: Record<string, unknown>, method = "POST") {
  const response = await fetch(path, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = (await response.json()) as Record<string, unknown>;
  if (!response.ok) {
    throw new Error(String(payload.error || payload.detail || "Request failed"));
  }
  return payload;
}

function ReceiptDialog({ open, onOpenChange, payload }: { open: boolean; onOpenChange: (open: boolean) => void; payload: Receipt }) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-[rgba(30,41,59,0.48)]" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[min(92vw,720px)] -translate-x-1/2 -translate-y-1/2 rounded-[28px] border-2 border-[var(--border)] bg-white p-6 shadow-[8px_8px_0_0_#1e293b] focus:outline-none">
          <Dialog.Title className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold">Latest control-plane receipt</Dialog.Title>
          <Dialog.Description className="mt-2 text-sm text-[var(--muted-foreground)]">
            This is the command record or pairing payload returned by the hosted app layer.
          </Dialog.Description>
          <pre className="mt-4 max-h-[420px] overflow-auto rounded-[24px] border-2 border-[var(--border)] bg-[var(--muted)] p-4 text-xs leading-6 text-[var(--foreground)]">
            {payload ? JSON.stringify(payload, null, 2) : "No payload yet."}
          </pre>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function CommandResultBanner({ error }: { error: string | null }) {
  if (!error) {
    return null;
  }
  return (
    <div className="flex items-start gap-3 rounded-[20px] border-2 border-[var(--border)] bg-[color:rgba(244,114,182,0.18)] px-4 py-3 text-sm">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2.5} />
      <span>{error}</span>
    </div>
  );
}

function useSubmissionState() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<Receipt>(null);
  const [receiptOpen, setReceiptOpen] = useState(false);

  async function run<T>(callback: () => Promise<T>) {
    setPending(true);
    setError(null);
    try {
      const payload = await callback();
      setReceipt(payload as Receipt);
      setReceiptOpen(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unknown request failure");
    } finally {
      setPending(false);
    }
  }

  return {
    pending,
    error,
    receipt,
    receiptOpen,
    setReceiptOpen,
    run,
  };
}

export function PairingWizard() {
  const [pairingCode, setPairingCode] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [deviceLabel, setDeviceLabel] = useState("Primary workstation");
  const state = useSubmissionState();

  return (
    <StickerCard tone="quaternary" icon={<Link2 className="h-5 w-5" strokeWidth={2.5} />}>
      <div className="space-y-4">
        <div>
          <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Pairing wizard</p>
          <h3 className="mt-2 font-[family-name:var(--font-outfit)] text-2xl font-extrabold">Connect a local Skylattice agent</h3>
        </div>
        <p className="text-sm leading-7 text-[var(--muted-foreground)]">
          Generate a short-lived pairing code in the hosted app, then claim it locally with the CLI connector so the browser never needs direct localhost access.
        </p>
        <CommandResultBanner error={state.error} />
        <div className="flex flex-wrap gap-3">
          <CandyButton
            onClick={() =>
              state.run(async () => {
                const payload = await submitJson("/api/control-plane/pairings");
                setPairingCode(String(payload.pairingCode));
                setExpiresAt(String(payload.expiresAt));
                return payload;
              })
            }
            disabled={state.pending}
          >
            {state.pending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" strokeWidth={2.5} />}
            Generate pairing code
          </CandyButton>
        </div>
        {pairingCode ? (
          <div className="space-y-3 rounded-[24px] border-2 border-[var(--border)] bg-white p-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5" strokeWidth={2.5} />
              <span className="font-bold">Pairing code: {pairingCode}</span>
            </div>
            <p className="text-sm text-[var(--muted-foreground)]">Expires at {expiresAt}</p>
            <label className="block text-sm font-bold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
              Suggested device label
              <input
                className="focus-pop mt-2 block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base"
                value={deviceLabel}
                onChange={(event) => setDeviceLabel(event.target.value)}
              />
            </label>
            <pre className="overflow-auto rounded-[20px] border-2 border-[var(--border)] bg-[var(--muted)] p-4 text-xs leading-6">
{`skylattice web pair --control-plane-url ${APP_BASE_URL} --code ${pairingCode} --device-label "${deviceLabel}"`}
            </pre>
          </div>
        ) : null}
      </div>
      <ReceiptDialog open={state.receiptOpen} onOpenChange={state.setReceiptOpen} payload={state.receipt} />
    </StickerCard>
  );
}

export function PairingStatePanel({
  pairings,
  devices,
}: {
  pairings: PairingChallenge[];
  devices: PairedDevice[];
}) {
  return (
    <StickerCard tone="white" icon={<Link2 className="h-5 w-5" strokeWidth={2.5} />}>
      <div className="space-y-5 pt-7">
        <div>
          <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Current state</p>
          <h3 className="mt-2 font-[family-name:var(--font-outfit)] text-2xl font-extrabold">Pairing codes and connected devices</h3>
          <p className="mt-2 text-sm leading-7 text-[var(--muted-foreground)]">
            This panel makes onboarding less mysterious by showing the short-lived codes you created and the devices that already claimed one.
          </p>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <div className="space-y-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Recent pairing codes</p>
            {pairings.length ? (
              pairings.map((pairing) => (
                <div key={pairing.pairingId} className="rounded-[20px] border-2 border-[var(--border)] bg-[var(--muted)] px-4 py-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusChip tone={pairing.claimedAt ? "quaternary" : "tertiary"}>
                      {pairing.claimedAt ? "claimed" : "pending"}
                    </StatusChip>
                    <span className="font-bold">{pairing.pairingCode}</span>
                  </div>
                  <div className="mt-3 space-y-1 text-xs leading-6 text-[var(--muted-foreground)]">
                    <p>created {pairing.createdAt}</p>
                    <p>expires {pairing.expiresAt}</p>
                    {pairing.deviceLabel ? <p>device {pairing.deviceLabel}</p> : null}
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-[20px] border-2 border-dashed border-[var(--border)] bg-white px-4 py-4 text-sm text-[var(--muted-foreground)]">
                No pairing codes yet. Generate one from the wizard to start the browser-to-local bridge flow.
              </div>
            )}
          </div>
          <div className="space-y-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Connected devices</p>
            {devices.length ? (
              devices.map((device) => (
                <div key={device.deviceId} className="rounded-[20px] border-2 border-[var(--border)] bg-[var(--muted)] px-4 py-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusChip tone={device.online ? "quaternary" : "secondary"}>
                      {device.online ? "online" : "offline"}
                    </StatusChip>
                    <span className="font-bold">{device.label}</span>
                  </div>
                  <div className="mt-3 space-y-1 text-xs leading-6 text-[var(--muted-foreground)]">
                    <p>{device.deviceId}</p>
                    <p>bridge {device.bridgeBaseUrl}</p>
                    {device.lastSeenAt ? <p>last seen {device.lastSeenAt}</p> : <p>no heartbeat yet</p>}
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-[20px] border-2 border-dashed border-[var(--border)] bg-white px-4 py-4 text-sm text-[var(--muted-foreground)]">
                No devices have claimed a code yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </StickerCard>
  );
}

export function TaskCommandComposer({ devices }: { devices: PairedDevice[] }) {
  const [goal, setGoal] = useState("Refresh the README and prepare a draft PR.");
  const [deviceId, setDeviceId] = useState<string>(devices[0]?.deviceId || "");
  const [allowRepoWrite, setAllowRepoWrite] = useState(true);
  const [allowExternalWrite, setAllowExternalWrite] = useState(false);
  const state = useSubmissionState();

  return (
    <StickerCard tone="secondary" icon={<ShieldCheck className="h-5 w-5" strokeWidth={2.5} />}>
      <div className="space-y-4">
        <h3 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold">Queue a governed task run</h3>
        <textarea
          className="focus-pop min-h-32 w-full rounded-[20px] border-2 border-[var(--border-soft)] bg-white px-4 py-4 text-base leading-7"
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
        />
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm font-bold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
            Target device
            <select
              className="focus-pop mt-2 block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base"
              value={deviceId}
              onChange={(event) => setDeviceId(event.target.value)}
            >
              <option value="">Auto-pick latest device</option>
              {devices.map((device) => (
                <option key={device.deviceId} value={device.deviceId}>
                  {device.label}
                </option>
              ))}
            </select>
          </label>
          <div className="space-y-3 rounded-[20px] border-2 border-[var(--border)] bg-white p-4">
            <label className="flex items-center gap-3 text-sm font-medium">
              <input checked={allowRepoWrite} onChange={(event) => setAllowRepoWrite(event.target.checked)} type="checkbox" />
              Allow repo-write
            </label>
            <label className="flex items-center gap-3 text-sm font-medium">
              <input checked={allowExternalWrite} onChange={(event) => setAllowExternalWrite(event.target.checked)} type="checkbox" />
              Allow external-write
            </label>
          </div>
        </div>
        <CommandResultBanner error={state.error} />
        <CandyButton
          onClick={() =>
            state.run(() =>
              submitJson("/api/control-plane/commands", {
                kind: "task.run",
                deviceId: deviceId || undefined,
                payload: {
                  goal,
                  allowRepoWrite,
                  allowExternalWrite,
                },
              }),
            )
          }
          disabled={state.pending}
        >
          {state.pending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" strokeWidth={2.5} />}
          Queue task command
        </CandyButton>
      </div>
      <ReceiptDialog open={state.receiptOpen} onOpenChange={state.setReceiptOpen} payload={state.receipt} />
    </StickerCard>
  );
}

export function RadarCommandPanel({ devices }: { devices: PairedDevice[] }) {
  const [deviceId, setDeviceId] = useState<string>(devices[0]?.deviceId || "");
  const [scheduleId, setScheduleId] = useState("weekly-github");
  const [candidateId, setCandidateId] = useState("cand-seed");
  const [promotionId, setPromotionId] = useState("promotion-seed");
  const state = useSubmissionState();
  const common = useMemo(() => ({ deviceId: deviceId || undefined }), [deviceId]);

  return (
    <StickerCard tone="tertiary" icon={<Radar className="h-5 w-5" strokeWidth={2.5} />}>
      <div className="space-y-4">
        <h3 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold">Drive radar from the browser</h3>
        <label className="text-sm font-bold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
          Target device
          <select
            className="focus-pop mt-2 block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base"
            value={deviceId}
            onChange={(event) => setDeviceId(event.target.value)}
          >
            <option value="">Auto-pick latest device</option>
            {devices.map((device) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label}
              </option>
            ))}
          </select>
        </label>
        <Tabs.Root defaultValue="scan">
          <Tabs.List className="flex flex-wrap gap-2">
            {["scan", "schedule", "validate", "replay", "rollback"].map((item) => (
              <Tabs.Trigger
                key={item}
                value={item}
                className="focus-pop rounded-full border-2 border-[var(--border)] bg-white px-4 py-2 text-sm font-bold uppercase tracking-[0.12em] data-[state=active]:bg-[var(--accent)] data-[state=active]:text-white"
              >
                {item}
              </Tabs.Trigger>
            ))}
          </Tabs.List>
          <div className="mt-4 rounded-[24px] border-2 border-[var(--border)] bg-white p-4">
            <Tabs.Content value="scan" className="space-y-3">
              <p className="text-sm text-[var(--muted-foreground)]">Queue a manual weekly-style scan against the paired local runtime.</p>
              <CandyButton onClick={() => state.run(() => submitJson("/api/control-plane/commands", { kind: "radar.scan", payload: { window: "manual", limit: 20 }, ...common }))}>
                Queue radar scan
              </CandyButton>
            </Tabs.Content>
            <Tabs.Content value="schedule" className="space-y-3">
              <label className="block text-sm font-bold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
                Schedule ID
                <input className="focus-pop mt-2 block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={scheduleId} onChange={(event) => setScheduleId(event.target.value)} />
              </label>
              <CandyButton onClick={() => state.run(() => submitJson("/api/control-plane/commands", { kind: "radar.schedule.run", payload: { scheduleId }, ...common }))}>
                Queue schedule run
              </CandyButton>
            </Tabs.Content>
            <Tabs.Content value="validate" className="space-y-3">
              <label className="block text-sm font-bold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
                Schedule ID
                <input className="focus-pop mt-2 block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={scheduleId} onChange={(event) => setScheduleId(event.target.value)} />
              </label>
              <CandyButton onClick={() => state.run(() => submitJson("/api/control-plane/commands", { kind: "radar.schedule.validate", payload: { scheduleId }, ...common }))}>
                Validate latest scheduled run
              </CandyButton>
            </Tabs.Content>
            <Tabs.Content value="replay" className="space-y-3">
              <label className="block text-sm font-bold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
                Candidate ID
                <input className="focus-pop mt-2 block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={candidateId} onChange={(event) => setCandidateId(event.target.value)} />
              </label>
              <CandyButton onClick={() => state.run(() => submitJson("/api/control-plane/commands", { kind: "radar.candidate.replay", payload: { candidateId }, ...common }))}>
                Replay candidate
              </CandyButton>
            </Tabs.Content>
            <Tabs.Content value="rollback" className="space-y-3">
              <label className="block text-sm font-bold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
                Promotion ID
                <input className="focus-pop mt-2 block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={promotionId} onChange={(event) => setPromotionId(event.target.value)} />
              </label>
              <CandyButton onClick={() => state.run(() => submitJson("/api/control-plane/commands", { kind: "radar.promotion.rollback", payload: { promotionId }, ...common }))}>
                Queue rollback
              </CandyButton>
            </Tabs.Content>
          </div>
        </Tabs.Root>
        <CommandResultBanner error={state.error} />
      </div>
      <ReceiptDialog open={state.receiptOpen} onOpenChange={state.setReceiptOpen} payload={state.receipt} />
    </StickerCard>
  );
}

export function MemoryCommandPanel({ devices }: { devices: PairedDevice[] }) {
  const [deviceId, setDeviceId] = useState<string>(devices[0]?.deviceId || "");
  const [query, setQuery] = useState("governance");
  const [recordId, setRecordId] = useState("record-seed");
  const [profileKey, setProfileKey] = useState("operator_style");
  const [profileValue, setProfileValue] = useState("concise, architecture-first");
  const [reason, setReason] = useState("Match the hosted control-plane default tone.");
  const state = useSubmissionState();
  const common = useMemo(() => ({ deviceId: deviceId || undefined }), [deviceId]);

  return (
    <StickerCard tone="accent" icon={<Sparkles className="h-5 w-5" strokeWidth={2.5} />}>
      <div className="space-y-4">
        <h3 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold">Search and review memory from the app</h3>
        <label className="text-sm font-bold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
          Target device
          <select
            className="focus-pop mt-2 block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base"
            value={deviceId}
            onChange={(event) => setDeviceId(event.target.value)}
          >
            <option value="">Auto-pick latest device</option>
            {devices.map((device) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label}
              </option>
            ))}
          </select>
        </label>
        <Tabs.Root defaultValue="search">
          <Tabs.List className="flex flex-wrap gap-2">
            {["search", "profile", "confirm", "reject"].map((item) => (
              <Tabs.Trigger
                key={item}
                value={item}
                className="focus-pop rounded-full border-2 border-[var(--border)] bg-white px-4 py-2 text-sm font-bold uppercase tracking-[0.12em] data-[state=active]:bg-[var(--accent)] data-[state=active]:text-white"
              >
                {item}
              </Tabs.Trigger>
            ))}
          </Tabs.List>
          <div className="mt-4 rounded-[24px] border-2 border-[var(--border)] bg-white p-4">
            <Tabs.Content value="search" className="space-y-3">
              <input className="focus-pop block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={query} onChange={(event) => setQuery(event.target.value)} />
              <CandyButton onClick={() => state.run(() => submitJson("/api/control-plane/commands", { kind: "memory.search", payload: { query, limit: 5 }, ...common }))}>
                Queue memory search
              </CandyButton>
            </Tabs.Content>
            <Tabs.Content value="profile" className="space-y-3">
              <input className="focus-pop block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={profileKey} onChange={(event) => setProfileKey(event.target.value)} />
              <input className="focus-pop block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={profileValue} onChange={(event) => setProfileValue(event.target.value)} />
              <textarea className="focus-pop block min-h-24 w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={reason} onChange={(event) => setReason(event.target.value)} />
              <CandyButton onClick={() => state.run(() => submitJson("/api/control-plane/commands", { kind: "memory.profile.propose", payload: { key: profileKey, value: profileValue, reason }, ...common }))}>
                Queue profile proposal
              </CandyButton>
            </Tabs.Content>
            <Tabs.Content value="confirm" className="space-y-3">
              <input className="focus-pop block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={recordId} onChange={(event) => setRecordId(event.target.value)} />
              <CandyButton onClick={() => state.run(() => submitJson("/api/control-plane/commands", { kind: "memory.review.confirm", payload: { recordId }, ...common }))}>
                Confirm proposal
              </CandyButton>
            </Tabs.Content>
            <Tabs.Content value="reject" className="space-y-3">
              <input className="focus-pop block w-full rounded-[18px] border-2 border-[var(--border-soft)] bg-white px-4 py-3 text-base" value={recordId} onChange={(event) => setRecordId(event.target.value)} />
              <CandyButton onClick={() => state.run(() => submitJson("/api/control-plane/commands", { kind: "memory.review.reject", payload: { recordId }, ...common }))}>
                Reject proposal
              </CandyButton>
            </Tabs.Content>
          </div>
        </Tabs.Root>
        <CommandResultBanner error={state.error} />
      </div>
      <ReceiptDialog open={state.receiptOpen} onOpenChange={state.setReceiptOpen} payload={state.receipt} />
    </StickerCard>
  );
}

export function DeviceManager({ devices }: { devices: PairedDevice[] }) {
  const [localDevices, setLocalDevices] = useState(devices);
  const state = useSubmissionState();

  return (
    <StickerCard tone="white" icon={<Link2 className="h-5 w-5" strokeWidth={2.5} />}>
      <div className="space-y-4 pt-7">
        <h3 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold">Paired devices</h3>
        <p className="text-sm leading-7 text-[var(--muted-foreground)]">
          Revoke a device if you want to cut off a connector token or move browser control to a different machine.
        </p>
        <CommandResultBanner error={state.error} />
        <div className="space-y-3">
          {localDevices.length ? (
            localDevices.map((device) => (
              <div key={device.deviceId} className="rounded-[20px] border-2 border-[var(--border)] bg-white px-4 py-4 shadow-[var(--shadow-hard)]">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div className="space-y-1">
                    <p className="font-bold">{device.label}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">{device.deviceId}</p>
                      <p className="text-xs text-[var(--muted-foreground)]">
                        {device.online ? "Online" : "Offline"} {device.lastSeenAt ? `- last seen ${device.lastSeenAt}` : ""}
                      </p>
                    <p className="text-xs text-[var(--muted-foreground)]">bridge {device.bridgeBaseUrl}</p>
                    {device.latestKernelStatus ? (
                      <p className="text-xs text-[var(--muted-foreground)]">kernel {device.latestKernelStatus}</p>
                    ) : null}
                    {device.latestAuthSummary ? (
                      <p className="text-xs leading-6 text-[var(--muted-foreground)]">{device.latestAuthSummary}</p>
                    ) : null}
                  </div>
                  <CandyButton
                    variant="secondary"
                    onClick={() =>
                      state.run(async () => {
                        const payload = await submitJson(`/api/control-plane/devices/${device.deviceId}`, undefined, "DELETE");
                        setLocalDevices((current) => current.filter((item) => item.deviceId !== device.deviceId));
                        return payload;
                      })
                    }
                    disabled={state.pending}
                  >
                    {state.pending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" strokeWidth={2.5} />}
                    Revoke
                  </CandyButton>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-[20px] border-2 border-dashed border-[var(--border)] bg-[var(--muted)] px-4 py-4 text-sm text-[var(--muted-foreground)]">
              No paired devices yet.
            </div>
          )}
        </div>
      </div>
      <ReceiptDialog open={state.receiptOpen} onOpenChange={state.setReceiptOpen} payload={state.receipt} />
    </StickerCard>
  );
}

export function DeviceReadinessPanel({ devices }: { devices: PairedDevice[] }) {
  return (
    <StickerCard tone="quaternary" icon={<Link2 className="h-5 w-5" strokeWidth={2.5} />}>
      <div className="space-y-4 pt-7">
        <h3 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold">Local agent readiness</h3>
        <p className="text-sm leading-7 text-[var(--muted-foreground)]">
          The hosted app only knows what the paired connector has most recently reported. This view is the browser-friendly version of the local `doctor/auth` heartbeat.
        </p>
        <div className="space-y-3">
          {devices.length ? (
            devices.map((device) => (
              <div key={device.deviceId} className="rounded-[20px] border-2 border-[var(--border)] bg-white px-4 py-4 shadow-[var(--shadow-hard)]">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusChip tone={device.online ? "quaternary" : "secondary"}>{device.online ? "online" : "offline"}</StatusChip>
                  {device.latestKernelStatus ? (
                    <StatusChip tone="tertiary">kernel {device.latestKernelStatus}</StatusChip>
                  ) : (
                    <StatusChip tone="tertiary">no kernel heartbeat yet</StatusChip>
                  )}
                </div>
                <p className="mt-3 font-bold">{device.label}</p>
                <p className="mt-1 text-xs text-[var(--muted-foreground)]">{device.deviceId}</p>
                <p className="mt-3 text-sm leading-7 text-[var(--foreground)]">
                  {device.latestAuthSummary || "No auth summary has been reported yet. Pair the device and run a connector heartbeat to populate provider readiness."}
                </p>
                <div className="mt-3 flex flex-wrap gap-3 text-xs text-[var(--muted-foreground)]">
                  <span>bridge {device.bridgeBaseUrl}</span>
                  {device.lastSeenAt ? <span>last seen {device.lastSeenAt}</span> : <span>never seen</span>}
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-[20px] border-2 border-dashed border-[var(--border)] bg-white px-4 py-4 text-sm text-[var(--muted-foreground)]">
              No paired devices yet, so the hosted app cannot report live local readiness.
            </div>
          )}
        </div>
      </div>
    </StickerCard>
  );
}

export function ApprovalManager({ approvals }: { approvals: ApprovalRecord[] }) {
  const [localApprovals, setLocalApprovals] = useState(approvals);
  const state = useSubmissionState();

  return (
    <StickerCard tone="secondary" icon={<ShieldCheck className="h-5 w-5" strokeWidth={2.5} />}>
      <div className="space-y-4 pt-7">
        <h3 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold text-white">Approval queue</h3>
        <p className="text-sm leading-7 text-white">
          The hosted app can reflect approval pressure, but resolving it here still only closes the control-plane reminder. It does not bypass local runtime enforcement.
        </p>
        <CommandResultBanner error={state.error} />
        <div className="space-y-3">
          {localApprovals.length ? (
            localApprovals.map((approval) => (
              <div key={approval.approvalId} className="rounded-[20px] border-2 border-[var(--border)] bg-white px-4 py-4 text-[var(--foreground)] shadow-[var(--shadow-hard)]">
                <p className="font-bold">{approval.summary}</p>
                <p className="mt-2 text-xs text-[var(--muted-foreground)]">{approval.requiredFlags.join(", ")}</p>
                <div className="mt-4 flex items-center gap-3">
                  <CandyButton
                    variant="secondary"
                    onClick={() =>
                      state.run(async () => {
                        const payload = await submitJson(`/api/control-plane/approvals/${approval.approvalId}/resolve`);
                        setLocalApprovals((current) => current.filter((item) => item.approvalId !== approval.approvalId));
                        return payload;
                      })
                    }
                    disabled={state.pending}
                  >
                    {state.pending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" strokeWidth={2.5} />}
                    Resolve reminder
                  </CandyButton>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-[20px] border-2 border-dashed border-white/70 bg-white/10 px-4 py-4 text-sm text-white/90">
              No pending approval reminders.
            </div>
          )}
        </div>
      </div>
      <ReceiptDialog open={state.receiptOpen} onOpenChange={state.setReceiptOpen} payload={state.receipt} />
    </StickerCard>
  );
}

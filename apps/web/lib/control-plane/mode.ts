export type ControlPlaneMode = "preview" | "blocked" | "development" | "live-unpaired" | "live-ready";

export interface ControlPlaneModeInput {
  previewMode: boolean;
  blocked: boolean;
  hostedAlpha: boolean;
  deviceCount: number;
}

export interface CommandComposerGate {
  disabled: boolean;
  eyebrow: string;
  detail: string;
  actionHref?: string;
  actionLabel?: string;
}

export function resolveControlPlaneMode({
  previewMode,
  blocked,
  hostedAlpha,
  deviceCount,
}: ControlPlaneModeInput): ControlPlaneMode {
  if (previewMode) {
    return "preview";
  }
  if (blocked) {
    return "blocked";
  }
  if (!hostedAlpha) {
    return "development";
  }
  return deviceCount > 0 ? "live-ready" : "live-unpaired";
}

export function controlPlaneModeLabel(mode: ControlPlaneMode): string {
  if (mode === "preview") {
    return "Preview";
  }
  if (mode === "blocked") {
    return "Hosted Alpha blocked";
  }
  if (mode === "development") {
    return "Local development";
  }
  if (mode === "live-unpaired") {
    return "Live, unpaired";
  }
  return "Live and paired";
}

export function controlPlaneModeSummary(mode: ControlPlaneMode): string {
  if (mode === "preview") {
    return "Read-only sample data is visible; no live command can run from this browser session.";
  }
  if (mode === "blocked") {
    return "Hosted Alpha semantics are active, but required deployment configuration is missing.";
  }
  if (mode === "development") {
    return "The app is using the local development control-plane surface, not a public Hosted Alpha deployment.";
  }
  if (mode === "live-unpaired") {
    return "Sign-in and hosted persistence are ready, but a local Skylattice agent still needs to pair before execution is possible.";
  }
  return "The browser can queue intent for a paired local Skylattice agent, which still owns execution and governance.";
}

export function commandComposerGate(mode: ControlPlaneMode, deviceCount: number, signedIn = true): CommandComposerGate {
  if (mode === "preview") {
    return {
      disabled: true,
      eyebrow: "Preview mode",
      detail: "This workspace is read-only sample data. Sign in and pair a local Skylattice agent before queueing live commands.",
      actionHref: "/signin",
      actionLabel: "Sign in for Hosted Alpha",
    };
  }
  if (mode === "blocked") {
    return {
      disabled: true,
      eyebrow: "Hosted Alpha blocked",
      detail: "Live commands stay disabled until the public app URL, GitHub OAuth, and Postgres-backed control-plane state are configured.",
      actionHref: "/settings",
      actionLabel: "Review deployment blockers",
    };
  }
  if (deviceCount === 0) {
    return {
      disabled: true,
      eyebrow: "Pairing required",
      detail: "The browser can only write command intent after a local Skylattice agent is paired. Pair a device first; execution still happens locally.",
      actionHref: "/connect",
      actionLabel: "Pair a local agent",
    };
  }
  if (!signedIn) {
    return {
      disabled: true,
      eyebrow: "Sign-in required",
      detail: "A local agent is paired, but GitHub sign-in is required before this browser can create live command records. Execution still stays local after sign-in.",
      actionHref: "/signin",
      actionLabel: "Sign in with GitHub",
    };
  }
  return {
    disabled: false,
    eyebrow: "Ready to queue intent",
    detail: "Commands created here enter the hosted ledger and are claimed by a paired local connector for execution.",
    actionHref: "/commands",
    actionLabel: "Open command ledger",
  };
}

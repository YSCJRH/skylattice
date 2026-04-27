import type { Metadata } from "next";
import Link from "next/link";

import { AppStatusBanner, AppWordmark, ButtonLink, PageFrame, StatusChip } from "@/components/ui";
import { getAppSession, getSessionUserId, isGuestUserId } from "@/lib/auth";
import { resolveControlPlaneMode } from "@/lib/control-plane/mode";
import { toPublicDevices } from "@/lib/control-plane/public";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import { DOCS_URL, GITHUB_REPOSITORY_URL, hostedAlphaReadiness, isDemoPreviewEnabled } from "@/lib/env";

import "./globals.css";

export const metadata: Metadata = {
  title: "Skylattice App",
  description: "Hosted control-plane surface for the local-first Skylattice runtime.",
};

const navigation = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/commands", label: "Commands" },
  { href: "/tasks", label: "Tasks" },
  { href: "/radar", label: "Radar" },
  { href: "/memory", label: "Memory" },
  { href: "/connect", label: "Connect" },
  { href: "/settings", label: "Settings" },
];

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const session = await getAppSession();
  const userId = await getSessionUserId();
  const signedIn = !isGuestUserId(userId);
  const demoPreview = isDemoPreviewEnabled() && isGuestUserId(userId);
  const store = getControlPlaneStore();
  const persistence = store.describePersistence();
  const readiness = hostedAlphaReadiness();
  const blocked = persistence.backend === "blocked";
  const snapshot = blocked ? null : await store.getDashboardSnapshot(userId);
  const devices = snapshot ? toPublicDevices(snapshot.devices) : [];
  const mode = resolveControlPlaneMode({
    previewMode: demoPreview,
    blocked,
    hostedAlpha: readiness.hostedAlpha,
    deviceCount: devices.length,
  });
  const pairedActionHref = devices.length ? (signedIn ? "/commands" : "/signin") : "/connect";
  const pairedActionLabel = devices.length ? (signedIn ? "Open command center" : "Sign in with GitHub") : "Pair a local agent";

  return (
    <html lang="en">
      <body className="font-[family-name:var(--font-plus-jakarta-sans)]">
        <PageFrame>
          <header className="mb-10 rounded-[28px] border-2 border-[var(--border)] bg-white/85 px-5 py-4 shadow-[var(--shadow-soft)] backdrop-blur-sm">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center justify-between gap-4">
                <AppWordmark />
                <Link href={DOCS_URL} className="rounded-full border-2 border-[var(--border)] px-4 py-2 text-sm font-bold hover:bg-[var(--tertiary)] lg:hidden">
                  Docs
                </Link>
              </div>
              <nav className="flex flex-wrap gap-2">
                {navigation.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="rounded-full border-2 border-[var(--border)] bg-[var(--muted)] px-4 py-2 text-sm font-bold hover:bg-[var(--quaternary)]"
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
              <div className="flex flex-wrap items-center gap-2">
                {mode === "preview" ? <StatusChip tone="tertiary">preview</StatusChip> : null}
                {mode === "blocked" ? <StatusChip tone="secondary">hosted alpha blocked</StatusChip> : null}
                {mode === "live-unpaired" ? <StatusChip tone="secondary">pair local agent</StatusChip> : null}
                {mode === "live-ready" ? <StatusChip tone="quaternary">paired control</StatusChip> : null}
                {mode === "development" ? <StatusChip tone="accent">local development</StatusChip> : null}
                <Link href={DOCS_URL} className="hidden rounded-full border-2 border-[var(--border)] px-4 py-2 text-sm font-bold hover:bg-[var(--tertiary)] lg:inline-flex">
                  Docs
                </Link>
                <Link href={GITHUB_REPOSITORY_URL} className="rounded-full border-2 border-[var(--border)] px-4 py-2 text-sm font-bold hover:bg-[var(--secondary)] hover:text-white">
                  GitHub
                </Link>
                {session?.user ? (
                  <Link href="/api/auth/signout?callbackUrl=/" className="rounded-full border-2 border-[var(--border)] bg-[var(--accent)] px-4 py-2 text-sm font-bold text-white">
                    Sign out
                  </Link>
                ) : (
                  <Link href="/signin" className="rounded-full border-2 border-[var(--border)] bg-[var(--accent)] px-4 py-2 text-sm font-bold text-white">
                    Sign in
                  </Link>
                )}
              </div>
            </div>
          </header>
          {demoPreview ? (
            <AppStatusBanner
              mode={mode}
              title="Preview is showing representative sample data."
              description="You are inspecting the product shape with seeded commands, devices, pairings, and approvals. No paired local agent means no real execution from this browser session."
              chips={
                <>
                  <StatusChip tone="tertiary">read-only sample data</StatusChip>
                  <StatusChip tone="accent">local agent still required</StatusChip>
                </>
              }
              action={
                <ButtonLink href="/signin" variant="secondary">
                  Set up Hosted Alpha
                </ButtonLink>
              }
            />
          ) : null}
          {blocked ? (
            <AppStatusBanner
              mode={mode}
              title="Hosted Alpha is blocked by deployment configuration."
              description="This deployment is being treated like a real Hosted Alpha surface, so it refuses to fall back to local development persistence. Finish the public app URL, GitHub OAuth, and Postgres-backed env before expecting live browser control."
              blockers={readiness.blockers}
              chips={
                <>
                  <StatusChip tone="secondary">no local-file fallback</StatusChip>
                  <StatusChip tone="tertiary">browser is not runtime truth</StatusChip>
                </>
              }
              action={
                <ButtonLink href="/settings" variant="secondary">
                  Review blockers
                </ButtonLink>
              }
            />
          ) : null}
          {!demoPreview && !blocked && !readiness.hostedAlpha ? (
            <AppStatusBanner
              mode={mode}
              title="This is the local development control plane."
              description="You are using the same web product surface locally, but this session is not a real public Hosted Alpha deployment yet. Use preview for a read-only first look, or configure Hosted Alpha envs before treating this app like the public browser surface."
              chips={
                <>
                  <StatusChip tone="accent">{persistence.backend} backend</StatusChip>
                  <StatusChip tone={devices.length ? "quaternary" : "tertiary"}>
                    {devices.length ? `${devices.length} paired device(s)` : "pairing still recommended"}
                  </StatusChip>
                  <StatusChip tone="tertiary">not a public Hosted Alpha URL</StatusChip>
                </>
              }
              action={
                <ButtonLink href={pairedActionHref} variant="secondary">
                  {pairedActionLabel}
                </ButtonLink>
              }
            />
          ) : null}
          {!demoPreview && !blocked && readiness.hostedAlpha ? (
            <AppStatusBanner
              mode={mode}
              title={devices.length ? (signedIn ? "Hosted Alpha can route intent to paired local agents." : "Hosted Alpha has paired local agents, but sign-in is required.") : "Hosted Alpha is ready, but no local agent is paired yet."}
              description={devices.length
                ? signedIn
                  ? "This browser can queue task, radar, and memory intent, but the paired local connector still owns real execution, memory truth, and governance enforcement."
                  : "A paired local connector exists, but command creation still requires GitHub sign-in before the local runtime can claim work."
                : "GitHub sign-in and hosted persistence are ready, but real work still needs a paired local agent. Until then, the browser has nowhere truthful to send execution."}
              chips={
                <>
                  <StatusChip tone="quaternary">{devices.length ? `${devices.length} paired device(s)` : "0 paired devices"}</StatusChip>
                  <StatusChip tone="accent">{snapshot ? `${snapshot.commands.length} recent command(s)` : "0 recent commands"}</StatusChip>
                </>
              }
              action={
                <ButtonLink href={pairedActionHref} variant="secondary">
                  {pairedActionLabel}
                </ButtonLink>
              }
            />
          ) : null}
          {children}
        </PageFrame>
      </body>
    </html>
  );
}

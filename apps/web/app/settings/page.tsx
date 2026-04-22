import { DeviceManager } from "@/components/control-plane-panels";
import { ButtonLink, SectionHeading, StatusChip, StickerCard, WorkspaceHero } from "@/components/ui";
import { getAppSession } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import { DOCS_URL, GITHUB_REPOSITORY_URL, isGitHubAuthConfigured } from "@/lib/env";
import Link from "next/link";

export default async function SettingsPage() {
  const session = await getAppSession();
  const store = getControlPlaneStore();
  const persistence = store.describePersistence();
  const userId = session?.user?.email || session?.user?.name || "guest@skylattice.local";
  const devices = await store.listDevices(userId);

  return (
    <main className="space-y-8">
      <WorkspaceHero
        title="Settings and trust surfaces"
        description="This page makes the hosted control plane honest about auth, persistence mode, docs links, and the local-first boundaries it is intentionally not allowed to cross."
        chips={
          <>
            <StatusChip tone={isGitHubAuthConfigured() ? "quaternary" : "secondary"}>
              {isGitHubAuthConfigured() ? "GitHub auth ready" : "GitHub auth blocked"}
            </StatusChip>
            <StatusChip tone="tertiary">{persistence.backend}</StatusChip>
          </>
        }
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <StickerCard tone="white" className="px-8 py-8">
          <SectionHeading
            eyebrow="Identity"
            title="Account model"
            description={session?.user ? `Signed in as ${session.user.email || session.user.name}.` : "No active browser session. Sign in with GitHub to queue commands or pair devices."}
          />
        </StickerCard>
        <StickerCard tone="accent" className="px-8 py-8">
          <div className="space-y-4 text-white">
            <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-white/80">Persistence</p>
            <p className="font-[family-name:var(--font-outfit)] text-3xl font-extrabold">Current backend: {persistence.backend}</p>
            <p className="text-sm leading-7">
              The current same-repo scaffold stores hosted control-plane state in a local development file by default, but it can switch to the Postgres-ready backend when `DATABASE_URL` or `SKYLATTICE_CONTROL_PLANE_DATABASE_URL` is configured.
            </p>
          </div>
        </StickerCard>
      </div>
      <section className="grid gap-6 md:grid-cols-3">
        <StickerCard tone="tertiary">
          <div className="space-y-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Docs</p>
            <ButtonLink href={DOCS_URL}>Open canonical docs</ButtonLink>
          </div>
        </StickerCard>
        <StickerCard tone="secondary">
          <div className="space-y-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-white/80">Source</p>
            <ButtonLink href={GITHUB_REPOSITORY_URL} variant="secondary">
              Open repository
            </ButtonLink>
          </div>
        </StickerCard>
        <StickerCard tone="quaternary">
          <div className="space-y-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Connect</p>
            <ButtonLink href="/connect">Pair a device</ButtonLink>
          </div>
        </StickerCard>
      </section>
      <StickerCard tone="white" className="px-8 py-8">
        <SectionHeading
          eyebrow="Paired runtime management"
          title="Manage connector trust explicitly."
          description="Revoke devices here if a machine should stop receiving queued commands or if you want to rotate pairing without changing the hosted account."
          action={
            <Link
              href="/devices"
              className="rounded-full border-2 border-[var(--border)] bg-[var(--accent)] px-4 py-2 text-sm font-bold text-white shadow-[var(--shadow-hard)]"
            >
              Open devices page
            </Link>
          }
        />
      </StickerCard>
      <DeviceManager devices={devices} />
    </main>
  );
}

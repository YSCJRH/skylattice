import { DeviceManager } from "@/components/control-plane-panels";
import { ButtonLink, HostedAlphaNotice, PreviewNotice, SectionHeading, StatusChip, StickerCard, WorkspaceHero } from "@/components/ui";
import { getAppSession, getSessionUserId, isGuestUserId } from "@/lib/auth";
import { toPublicDevices } from "@/lib/control-plane/public";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import { DOCS_URL, GITHUB_REPOSITORY_URL, hostedAlphaReadiness, isDemoPreviewEnabled, isGitHubAuthConfigured } from "@/lib/env";
import Link from "next/link";

export default async function SettingsPage() {
  const session = await getAppSession();
  const store = getControlPlaneStore();
  const persistence = store.describePersistence();
  const userId = await getSessionUserId();
  const readiness = hostedAlphaReadiness();
  const blocked = persistence.backend === "blocked";
  const devices = blocked ? [] : toPublicDevices(await store.listDevices(userId));
  const previewMode = isDemoPreviewEnabled() && isGuestUserId(userId);

  return (
    <main className="space-y-8">
      {blocked ? (
        <HostedAlphaNotice
          description="This deployment is being treated as Hosted Alpha, so the app refuses to fall back to local-file control-plane state. Finish the live deployment env before expecting real browser operations."
          blockers={readiness.blockers}
        />
      ) : null}
      {previewMode ? (
        <PreviewNotice
          title="Settings preview"
          description="The preview keeps persistence, docs, and trust surfaces visible even before GitHub OAuth is configured. Live account and device management still require sign-in."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for Hosted Alpha settings
            </ButtonLink>
          }
        />
      ) : null}
      <WorkspaceHero
        title="Settings and trust surfaces"
        description="This page makes the hosted control plane honest about auth, persistence mode, docs links, and the local-first boundaries it is intentionally not allowed to cross."
        chips={
          <>
            <StatusChip tone={isGitHubAuthConfigured() ? "quaternary" : "secondary"}>
              {isGitHubAuthConfigured() ? "GitHub auth ready" : "GitHub auth blocked"}
            </StatusChip>
            <StatusChip tone={blocked ? "secondary" : "tertiary"}>{persistence.backend}</StatusChip>
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
              {blocked
                ? "Hosted Alpha mode is active, but the deployment is still missing the Postgres-backed control-plane env required for live operation."
                : "The current same-repo scaffold stores hosted control-plane state in a local development file by default, but it can switch to the Postgres-ready backend when `DATABASE_URL` or `SKYLATTICE_CONTROL_PLANE_DATABASE_URL` is configured."}
            </p>
          </div>
        </StickerCard>
      </div>
      <StickerCard tone="white" className="px-8 py-8">
        <SectionHeading
          eyebrow="Hosted alpha readiness"
          title={readiness.ready ? "Live deployment looks ready." : "Live deployment still has blockers."}
          description={readiness.ready ? "Public app URL, GitHub OAuth, Postgres-backed persistence, and auth callback configuration are all present." : readiness.blockers.join(" ")}
        />
      </StickerCard>
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
      <DeviceManager devices={devices} previewMode={previewMode || blocked} />
    </main>
  );
}

import { PairingStatePanel, PairingWizard } from "@/components/control-plane-panels";
import { ButtonLink, PreviewNotice, SectionHeading, StatusChip, StickerCard, WorkspaceHero } from "@/components/ui";
import { getSessionUserId, isGuestUserId } from "@/lib/auth";
import { getControlPlaneStore } from "@/lib/control-plane/store";
import { isDemoPreviewEnabled } from "@/lib/env";

export default async function ConnectPage() {
  const userId = await getSessionUserId();
  const snapshot = await getControlPlaneStore().getDashboardSnapshot(userId);
  const previewMode = isDemoPreviewEnabled() && isGuestUserId(userId);

  return (
    <main className="space-y-8">
      {previewMode ? (
        <PreviewNotice
          title="Preview pairing before you generate a real code."
          description="The preview shows representative pairing codes and connected devices so the onboarding flow is visible before GitHub sign-in or a live connector are configured."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for live pairing
            </ButtonLink>
          }
        />
      ) : null}
      <WorkspaceHero
        title="Pair your local Skylattice agent"
        description="The hosted control plane needs an authenticated local executor. Pairing is the bridge that keeps the browser and the local runtime separate."
        chips={
          <>
            <StatusChip tone="accent">short-lived code</StatusChip>
            <StatusChip tone="secondary">connector token</StatusChip>
            <StatusChip tone="quaternary">no localhost browser calls</StatusChip>
          </>
        }
      />
      <SectionHeading
        eyebrow="Onboarding"
        title="The first app loop starts with pairing, not blind cloud trust."
        description="This flow is shaped directly by the first-run friction questions already captured in GitHub issues #2 and #4: reduce confusion, keep trust visible, and make the next step obvious."
      />
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <PairingWizard previewMode={previewMode} />
        <StickerCard tone="white" className="px-8 py-8">
          <div className="space-y-4">
            <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Pairing contract</p>
            <ul className="space-y-3 text-sm leading-7 text-[var(--foreground)]">
              <li>Generate a code in the hosted app after GitHub sign-in.</li>
              <li>Claim that code from `skylattice web pair` on the local machine.</li>
              <li>Store connector credentials only in local state under `.local/`.</li>
              <li>Use connector heartbeats and command claims instead of browser-to-localhost RPC.</li>
            </ul>
          </div>
        </StickerCard>
      </div>
      <PairingStatePanel pairings={snapshot.pairings} devices={snapshot.devices} />
    </main>
  );
}

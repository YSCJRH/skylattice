import { PairingStatePanel, PairingWizard } from "@/components/control-plane-panels";
import { ButtonLink, HostedAlphaNotice, PreviewNotice, SectionHeading, StatusChip, StickerCard, WorkspaceHero } from "@/components/ui";
import { getControlPlanePageContext } from "@/lib/control-plane/page-context";
import { toPublicDevices, toPublicPairings } from "@/lib/control-plane/public";

export default async function ConnectPage() {
  const context = await getControlPlanePageContext();
  const { snapshot, previewMode, blocked, readiness, signedIn } = context;
  const devices = toPublicDevices(snapshot.devices);
  const pairings = toPublicPairings(snapshot.pairings);
  const onboardingSteps = [
    "Sign in through the hosted app so pairing belongs to the right account.",
    "Generate a short-lived pairing code in this browser.",
    "Claim the code locally with `skylattice web pair` on the machine that will execute work.",
    "Run connector heartbeat or polling so commands can be claimed and readiness becomes visible.",
  ];

  return (
    <main className="space-y-8">
      {blocked ? (
        <HostedAlphaNotice
          description="Live pairing is unavailable until the hosted control-plane deployment has a public app URL, GitHub OAuth, and Postgres-backed state configured."
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
          title="Preview pairing before you generate a real code."
          description="The preview shows representative pairing codes and connected devices so the onboarding flow is visible before GitHub sign-in or a live connector are configured."
          action={
            <ButtonLink href="/signin" variant="secondary">
              Sign in for Hosted Alpha pairing
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
        description="Pairing is the trust handshake that turns a browser session into a control cockpit without moving execution, memory, or governance into the cloud."
      />
      <section className="grid gap-4 md:grid-cols-4">
        {onboardingSteps.map((step, index) => (
          <StickerCard key={step} tone={index === 2 ? "quaternary" : "white"}>
            <div className="space-y-3">
              <StatusChip tone={index === 2 ? "quaternary" : "tertiary"}>step {index + 1}</StatusChip>
              <p className="text-sm leading-7 text-[var(--foreground)]">{step}</p>
            </div>
          </StickerCard>
        ))}
      </section>
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <PairingWizard previewMode={previewMode || blocked} signInRequired={!signedIn && !previewMode && !blocked} />
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
      <PairingStatePanel pairings={pairings} devices={devices} />
    </main>
  );
}

import { ArrowRight, GitBranch, NotebookText, ShieldCheck } from "lucide-react";

import { ButtonLink, PageFrame, SectionHeading, StatusChip, StickerCard, WorkspaceHero } from "@/components/ui";
import { DOCS_URL } from "@/lib/env";

const productCards = [
  {
    title: "Hosted control plane, local truth",
    body: "Sign in from the browser, queue work, inspect runs, and keep the actual execution, memory, and approvals on your own paired Skylattice agent.",
    tone: "accent" as const,
    icon: <ShieldCheck className="h-5 w-5" strokeWidth={2.5} />,
  },
  {
    title: "Governed task operations",
    body: "Task run, resume, recovery review, and materialized edit inspection move into a real product surface without dropping the repo-write and external-write guards.",
    tone: "secondary" as const,
    icon: <GitBranch className="h-5 w-5" strokeWidth={2.5} />,
  },
  {
    title: "Radar and memory workspaces",
    body: "The app makes radar status, schedule validation, memory review, and profile proposals inspectable enough for daily use instead of only terminal fluency.",
    tone: "tertiary" as const,
    icon: <NotebookText className="h-5 w-5" strokeWidth={2.5} />,
  },
];

export default function HomePage() {
  return (
    <main className="space-y-12">
      <WorkspaceHero
        title="Skylattice becomes a real web product without giving up local-first runtime truth."
        description="This hosted app surface is the control plane for sign-in, pairing, onboarding, and authenticated command intent. Your actual runs, private memory, and governance gates still stay with your local Skylattice agent."
        chips={
          <>
            <StatusChip tone="accent">GitHub login first</StatusChip>
            <StatusChip tone="secondary">Personal accounts</StatusChip>
            <StatusChip tone="tertiary">Browser queues intent</StatusChip>
            <StatusChip tone="quaternary">Local agent executes</StatusChip>
          </>
        }
      />

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <StickerCard tone="white" className="dot-grid overflow-hidden px-8 py-8 md:px-10">
          <div className="max-w-2xl space-y-6">
            <SectionHeading
              eyebrow="Public app surface"
              title="Stable grid, wild decoration, and operator-grade clarity."
              description="The app uses a playful geometric system on purpose: big shapes, hard shadows, strong borders, and lively motion for the marketing shell; calmer structured surfaces once you enter the authenticated workspaces."
              action={<ButtonLink href="/signin">Sign in with GitHub</ButtonLink>}
            />
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-[24px] border-2 border-[var(--border)] bg-white px-5 py-4 shadow-[var(--shadow-hard)]">
                <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Trust chain</p>
                <p className="mt-3 text-sm leading-7">Docs, proof assets, release pages, CI, and runtime state stay visible. The app deep-links back to the canonical docs instead of replacing them.</p>
              </div>
              <div className="rounded-[24px] border-2 border-[var(--border)] bg-[color:rgba(52,211,153,0.18)] px-5 py-4 shadow-[var(--shadow-hard)]">
                <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Execution model</p>
                <p className="mt-3 text-sm leading-7">Your browser never has to call localhost. A paired local connector polls the hosted control plane and runs commands under the same governance rules as the CLI.</p>
              </div>
            </div>
          </div>
        </StickerCard>

        <StickerCard tone="quaternary" className="px-8 py-8 md:px-10">
          <div className="space-y-4">
            <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Start path</p>
            <h2 className="font-[family-name:var(--font-outfit)] text-4xl font-extrabold tracking-tight">From docs visitor to signed-in operator.</h2>
            <ol className="space-y-4 text-sm leading-7 text-[var(--foreground)]">
              <li className="rounded-[20px] border-2 border-[var(--border)] bg-white px-4 py-3 shadow-[var(--shadow-hard)]">1. Land on docs, proof, or release surfaces and trust the product story.</li>
              <li className="rounded-[20px] border-2 border-[var(--border)] bg-white px-4 py-3 shadow-[var(--shadow-hard)]">2. Sign in with GitHub and generate a short-lived pairing code.</li>
              <li className="rounded-[20px] border-2 border-[var(--border)] bg-white px-4 py-3 shadow-[var(--shadow-hard)]">3. Claim that pairing from your local connector and start queuing governed work.</li>
            </ol>
            <ButtonLink href="/connect" variant="secondary">
              Explore pairing flow
            </ButtonLink>
          </div>
        </StickerCard>
      </section>

      <section className="space-y-6">
        <SectionHeading
          eyebrow="What ships in the first app slice"
          title="Near-CLI parity for the highest-value daily workflows."
          description="The goal is not a decorative shell. The goal is a product surface that can actually drive task, radar, and memory work while keeping the local runtime authoritative."
        />
        <div className="grid gap-6 md:grid-cols-3">
          {productCards.map((item) => (
            <StickerCard key={item.title} tone={item.tone} icon={item.icon}>
              <div className="pt-7">
                <h3 className="font-[family-name:var(--font-outfit)] text-2xl font-extrabold">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-[var(--foreground)]">{item.body}</p>
              </div>
            </StickerCard>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <StickerCard tone="white" className="px-8 py-8">
          <SectionHeading
            eyebrow="Docs stay canonical"
            title="The app points back to proof instead of trying to hide uncertainty."
            description="Pages docs remain the public discoverability and evidence layer. The app should earn trust by linking back to architecture, governance, and proof surfaces whenever decisions matter."
            action={<ButtonLink href={DOCS_URL}>Open docs</ButtonLink>}
          />
        </StickerCard>
        <StickerCard tone="secondary" className="px-8 py-8">
          <div className="space-y-4">
            <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-white/80">Operator promise</p>
            <h3 className="font-[family-name:var(--font-outfit)] text-3xl font-extrabold text-white">No silent autonomy, even when the browser gets prettier.</h3>
            <p className="text-sm leading-7 text-white">
              Hosted UX cannot bypass local approvals. Dangerous writes still require the same explicit flags and the same local runtime enforcement.
            </p>
            <a
              href="/signin"
              className="inline-flex items-center gap-3 rounded-full border-2 border-[var(--border)] bg-white px-5 py-3 text-sm font-bold text-[var(--foreground)] shadow-[var(--shadow-hard)]"
            >
              Continue to app
              <ArrowRight className="h-4 w-4" strokeWidth={2.5} />
            </a>
          </div>
        </StickerCard>
      </section>
    </main>
  );
}

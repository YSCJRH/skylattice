import Link from "next/link";

import { ButtonLink, SectionHeading, StickerCard, StatusChip } from "@/components/ui";
import { getAppSession } from "@/lib/auth";
import { isGitHubAuthConfigured } from "@/lib/env";

export default async function SignInPage() {
  const session = await getAppSession();
  const configured = isGitHubAuthConfigured();

  return (
    <main className="space-y-8">
      <SectionHeading
        eyebrow="Identity"
        title="Sign in to the hosted control plane."
        description="GitHub is the first login provider because the current Skylattice operator loop already lives close to Git, PRs, issues, and repo truth surfaces."
      />
      <StickerCard tone="accent" className="px-8 py-8">
        <div className="space-y-4">
          <StatusChip tone={configured ? "quaternary" : "secondary"}>
            {configured ? "GitHub OAuth configured" : "GitHub OAuth blocked by missing env"}
          </StatusChip>
          {session?.user ? (
            <>
              <p className="text-sm leading-7 text-white">You are already signed in as {session.user.email || session.user.name || "current operator"}.</p>
              <ButtonLink href="/dashboard" variant="secondary">
                Open dashboard
              </ButtonLink>
            </>
          ) : configured ? (
            <Link
              href="/api/auth/signin/github?callbackUrl=/dashboard"
              className="focus-pop inline-flex min-h-12 items-center justify-center rounded-full border-2 border-[var(--border)] bg-white px-5 py-3 text-sm font-bold text-[var(--foreground)] shadow-[var(--shadow-hard)]"
            >
              Continue with GitHub
            </Link>
          ) : (
            <p className="text-sm leading-7 text-white">
              Set `GITHUB_ID`, `GITHUB_SECRET`, and `NEXTAUTH_SECRET` for the app workspace before enabling real GitHub sign-in.
            </p>
          )}
        </div>
      </StickerCard>
    </main>
  );
}

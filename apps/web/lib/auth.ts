import { getServerSession, type NextAuthOptions } from "next-auth";
import GitHubProvider from "next-auth/providers/github";

import { isGitHubAuthConfigured } from "@/lib/env";

export const GUEST_USER_ID = "guest@skylattice.local";

const providers = isGitHubAuthConfigured()
  ? [
      GitHubProvider({
        clientId: process.env.GITHUB_ID || "",
        clientSecret: process.env.GITHUB_SECRET || "",
      }),
    ]
  : [];

export const authOptions: NextAuthOptions = {
  providers,
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/signin",
  },
};

export async function getAppSession() {
  if (!isGitHubAuthConfigured()) {
    return null;
  }
  return getServerSession(authOptions);
}

export async function getSessionUserId(): Promise<string> {
  const session = await getAppSession();
  return session?.user?.email || session?.user?.name || GUEST_USER_ID;
}

export function isGuestUserId(userId: string): boolean {
  return userId === GUEST_USER_ID;
}

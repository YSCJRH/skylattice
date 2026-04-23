import { getServerSession, type NextAuthOptions } from "next-auth";
import GitHubProvider from "next-auth/providers/github";

import { isGitHubAuthConfigured } from "@/lib/env";

export const GUEST_USER_ID = "guest@skylattice.local";

type SessionUser = {
  id?: string;
  email?: string | null;
  name?: string | null;
};

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
  callbacks: {
    session({ session, token }) {
      if (session.user && token.sub) {
        (session.user as SessionUser).id = `github:${token.sub}`;
      }
      return session;
    },
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
  const user = session?.user as SessionUser | undefined;
  return user?.id || user?.email || user?.name || GUEST_USER_ID;
}

export function isGuestUserId(userId: string): boolean {
  return userId === GUEST_USER_ID;
}

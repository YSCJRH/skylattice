import { getServerSession, type NextAuthOptions } from "next-auth";
import GitHubProvider from "next-auth/providers/github";

import { isGitHubAuthConfigured } from "@/lib/env";

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
  return getServerSession(authOptions);
}

export async function getSessionUserId(): Promise<string> {
  const session = await getAppSession();
  return session?.user?.email || session?.user?.name || "guest@skylattice.local";
}

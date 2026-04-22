import type { Metadata } from "next";
import { Outfit, Plus_Jakarta_Sans } from "next/font/google";
import Link from "next/link";

import { AppWordmark, PageFrame } from "@/components/ui";
import { getAppSession } from "@/lib/auth";
import { DOCS_URL, GITHUB_REPOSITORY_URL } from "@/lib/env";

import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  weight: ["700", "800"],
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-plus-jakarta-sans",
  weight: ["400", "500", "700"],
});

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

  return (
    <html lang="en" className={`${outfit.variable} ${plusJakartaSans.variable}`}>
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
          {children}
        </PageFrame>
      </body>
    </html>
  );
}

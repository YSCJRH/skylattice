export const DOCS_URL = process.env.NEXT_PUBLIC_SKYLATTICE_DOCS_URL || "https://yscjrh.github.io/skylattice/";
const vercelUrl =
  process.env.NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL
  || process.env.VERCEL_PROJECT_PRODUCTION_URL
  || process.env.VERCEL_URL
  || "";

export const APP_BASE_URL = process.env.NEXT_PUBLIC_SKYLATTICE_APP_URL || (vercelUrl ? `https://${vercelUrl}` : "http://localhost:3000");
export const GITHUB_REPOSITORY_URL = "https://github.com/YSCJRH/skylattice";

export function isGitHubAuthConfigured(): boolean {
  return Boolean(process.env.GITHUB_ID && process.env.GITHUB_SECRET && process.env.NEXTAUTH_SECRET);
}

export function controlPlaneStatePath(): string {
  return process.env.SKYLATTICE_CONTROL_PLANE_STATE_PATH || "../../.local/state/web-control-plane.json";
}

export function controlPlaneDatabaseUrl(): string | null {
  return process.env.SKYLATTICE_CONTROL_PLANE_DATABASE_URL || process.env.DATABASE_URL || null;
}

export function isDemoPreviewEnabled(): boolean {
  const value = process.env.NEXT_PUBLIC_SKYLATTICE_DEMO_PREVIEW || process.env.SKYLATTICE_DEMO_PREVIEW || "";
  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
}

export function isLocalAppUrl(url: string = APP_BASE_URL): boolean {
  return /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(url);
}

export function isHostedAlphaEnvironment(): boolean {
  const explicit = process.env.SKYLATTICE_HOSTED_ALPHA || "";
  if (["1", "true", "yes", "on"].includes(explicit.toLowerCase())) {
    return true;
  }
  return process.env.VERCEL_ENV === "production";
}

export function requiresHostedAlphaPersistence(): boolean {
  return isHostedAlphaEnvironment() && !isDemoPreviewEnabled();
}

export function hostedAlphaReadiness() {
  const databaseReady = Boolean(controlPlaneDatabaseUrl());
  const authReady = isGitHubAuthConfigured();
  const publicAppUrlReady = !isLocalAppUrl();
  const nextAuthUrlReady = Boolean(process.env.NEXTAUTH_URL || (publicAppUrlReady ? APP_BASE_URL : ""));
  const blockers: string[] = [];

  if (!publicAppUrlReady) {
    blockers.push("NEXT_PUBLIC_SKYLATTICE_APP_URL still points at localhost.");
  }
  if (!authReady) {
    blockers.push("GitHub OAuth env vars are incomplete.");
  }
  if (!databaseReady) {
    blockers.push("DATABASE_URL or SKYLATTICE_CONTROL_PLANE_DATABASE_URL is missing.");
  }
  if (!nextAuthUrlReady) {
    blockers.push("NEXTAUTH_URL is missing for hosted auth callbacks.");
  }

  return {
    hostedAlpha: isHostedAlphaEnvironment(),
    publicAppUrlReady,
    authReady,
    databaseReady,
    nextAuthUrlReady,
    ready: publicAppUrlReady && authReady && databaseReady && nextAuthUrlReady,
    blockers,
  };
}

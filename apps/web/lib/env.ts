export const DOCS_URL = process.env.NEXT_PUBLIC_SKYLATTICE_DOCS_URL || "https://yscjrh.github.io/skylattice/";
export const APP_BASE_URL = process.env.NEXT_PUBLIC_SKYLATTICE_APP_URL || "http://localhost:3000";
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

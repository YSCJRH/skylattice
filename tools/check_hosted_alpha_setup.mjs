import process from "node:process";

function truthy(value) {
  return ["1", "true", "yes", "on"].includes(String(value || "").toLowerCase());
}

function appBaseUrl() {
  const vercelUrl = process.env.NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL
    || process.env.VERCEL_PROJECT_PRODUCTION_URL
    || process.env.VERCEL_URL
    || "";
  return process.env.NEXT_PUBLIC_SKYLATTICE_APP_URL || (vercelUrl ? `https://${vercelUrl}` : "http://localhost:3000");
}

function isLocalUrl(url) {
  return /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(url);
}

function isHostedAlphaEnvironment() {
  return truthy(process.env.SKYLATTICE_HOSTED_ALPHA) || process.env.VERCEL_ENV === "production";
}

function hostedAlphaReadiness() {
  const url = appBaseUrl();
  const publicAppUrlReady = !isLocalUrl(url);
  const authReady = Boolean(process.env.GITHUB_ID && process.env.GITHUB_SECRET && process.env.NEXTAUTH_SECRET);
  const databaseReady = Boolean(process.env.SKYLATTICE_CONTROL_PLANE_DATABASE_URL || process.env.DATABASE_URL);
  const nextAuthUrlReady = Boolean(process.env.NEXTAUTH_URL || (publicAppUrlReady ? url : ""));
  const blockers = [];

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
    appBaseUrl: url,
    publicAppUrlReady,
    authReady,
    databaseReady,
    nextAuthUrlReady,
    ready: publicAppUrlReady && authReady && databaseReady && nextAuthUrlReady,
    blockers,
  };
}

const payload = hostedAlphaReadiness();
console.log(JSON.stringify(payload, null, 2));

if (!payload.hostedAlpha) {
  console.error("Hosted Alpha mode is not active. Set SKYLATTICE_HOSTED_ALPHA=1 or run this in a production Vercel environment.");
  process.exit(1);
}

if (!payload.ready) {
  process.exit(1);
}

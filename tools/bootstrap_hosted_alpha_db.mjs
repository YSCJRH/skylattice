import { readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import { Pool } from "@neondatabase/serverless";

function resolveDatabaseUrl() {
  const cliValue = process.argv.find((item) => item.startsWith("--database-url="));
  return cliValue?.slice("--database-url=".length)
    || process.env.SKYLATTICE_CONTROL_PLANE_DATABASE_URL
    || process.env.DATABASE_URL
    || "";
}

function resolveSqlPath() {
  const cliValue = process.argv.find((item) => item.startsWith("--sql="));
  return cliValue?.slice("--sql=".length)
    || path.resolve(process.cwd(), "apps/web/sql/hosted-alpha-bootstrap.sql");
}

function parseStatements(sqlText) {
  return sqlText
    .split(/;\s*(?:\r?\n|$)/g)
    .map((statement) => statement.trim())
    .filter(Boolean);
}

const databaseUrl = resolveDatabaseUrl();
if (!databaseUrl) {
  console.error("Missing DATABASE_URL or SKYLATTICE_CONTROL_PLANE_DATABASE_URL.");
  process.exit(1);
}

const sqlPath = resolveSqlPath();
const sqlText = await readFile(sqlPath, "utf-8");
const statements = parseStatements(sqlText);

const pool = new Pool({ connectionString: databaseUrl });

try {
  for (const statement of statements) {
    await pool.query(statement);
  }
  console.log(JSON.stringify({
    status: "ok",
    statements: statements.length,
    sqlPath,
  }, null, 2));
} finally {
  await pool.end();
}

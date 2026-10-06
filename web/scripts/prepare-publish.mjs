import { cpSync, mkdirSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Isolate Sites' source repository from the user's existing repository.
const root = fileURLToPath(new URL("../", import.meta.url));
const destination = path.join(root, ".sites-runtime/publish");
const excluded = new Set([
  "node_modules",
  ".next",
  ".git",
  ".sites-runtime",
  "reports",
]);
mkdirSync(destination, { recursive: true });
for (const entry of readdirSync(root)) {
  if (
    excluded.has(entry) ||
    entry.startsWith(".env") ||
    entry.endsWith(".tsbuildinfo")
  )
    continue;
  cpSync(path.join(root, entry), path.join(destination, entry), {
    recursive: true,
    filter: (source) => !/\.sqlite(?:-wal|-shm)?$/.test(source),
  });
}
console.log(destination);

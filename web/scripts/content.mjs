import { DatabaseSync } from "node:sqlite";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
mkdirSync(path.join(root, "data"), { recursive: true });
mkdirSync(path.join(root, "src/generated"), { recursive: true });
const database = path.join(root, "data/pepones.sqlite");
const fresh = !existsSync(database);
const db = new DatabaseSync(database);
db.exec(
  "PRAGMA foreign_keys = ON; CREATE TABLE IF NOT EXISTS content (key TEXT PRIMARY KEY, value TEXT NOT NULL CHECK(json_valid(value)));",
);
if (fresh || process.argv.includes("--sync")) {
  const seed = JSON.parse(
    readFileSync(path.join(root, "data/content.json"), "utf8"),
  );
  db.exec("BEGIN");
  try {
    const insert = db.prepare(
      "INSERT INTO content(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
    );
    for (const [key, value] of Object.entries(seed))
      insert.run(key, JSON.stringify(value));
    db.exec("COMMIT");
  } catch (error) {
    db.exec("ROLLBACK");
    throw error;
  }
}
const content = Object.fromEntries(
  db
    .prepare("SELECT key,value FROM content")
    .all()
    .map((row) => [row.key, JSON.parse(row.value)]),
);
db.close();
if (!content.burgers.some((b) => b.id === content.weekly.burgerId))
  throw new Error("La semanal debe referenciar una hamburguesa existente.");
const ids = new Set(content.ingredients.map((i) => i.id));
for (const burger of content.burgers) {
  for (const id of burger.ingredients)
    if (!ids.has(id))
      throw new Error(`Ingrediente desconocido en ${burger.id}: ${id}`);
  for (const layer of burger.recipe)
    if (!ids.has(layer.ingredientId))
      throw new Error(`Ingrediente inexistente: ${layer.ingredientId}`);
  if (
    burger.price !== null &&
    (!Number.isFinite(burger.price) || burger.price < 0)
  )
    throw new Error(`Precio inválido: ${burger.id}`);
}
if (
  content.restaurant.whatsapp &&
  !/^\d{8,15}$/.test(content.restaurant.whatsapp)
)
  throw new Error("WhatsApp debe incluir país y solo dígitos.");
for (const key of ["startsAt", "endsAt"])
  if (
    content.weekly[key] &&
    (!Number.isFinite(Date.parse(content.weekly[key])) ||
      !/(Z|[+-]\d{2}:\d{2})$/.test(content.weekly[key]))
  )
    throw new Error(`${key} debe ser una fecha ISO con zona horaria.`);
if (
  !content.weekly.demo &&
  content.weekly.status === "available" &&
  (!content.weekly.startsAt || !content.weekly.endsAt)
)
  throw new Error("Una semanal real necesita fechas de inicio y fin.");
if (
  content.weekly.startsAt &&
  content.weekly.endsAt &&
  Date.parse(content.weekly.startsAt) >= Date.parse(content.weekly.endsAt)
)
  throw new Error("Vigencia inválida.");
writeFileSync(
  path.join(root, "src/generated/content.json"),
  JSON.stringify(content, null, 2) + "\n",
);
console.log("Contenido generado desde SQLite. La base de datos no se publica.");

import { readFile, writeFile, mkdir, copyFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import sharp from "sharp";

const web = fileURLToPath(new URL("../", import.meta.url));
const root = path.resolve(web, "..");
const source = path.join(root, "material/semanal/texas/modelos");
const models = path.join(web, "public/models/texas");
const images = path.join(web, "public/images/texas");

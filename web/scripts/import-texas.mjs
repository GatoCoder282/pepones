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
await mkdir(models, { recursive: true });
await mkdir(images, { recursive: true });
const manifest = JSON.parse(
  await readFile(path.join(source, "manifest.json"), "utf8"),
);

function readGlb(bytes, id) {
  assert.equal(bytes.toString("ascii", 0, 4), "glTF", `Invalid GLB: ${id}`);
  assert.equal(bytes.readUInt32LE(4), 2, "Expected glTF 2.0");
  assert.equal(bytes.readUInt32LE(8), bytes.length, "Incomplete GLB");
  return JSON.parse(bytes.toString("utf8", 20, 20 + bytes.readUInt32LE(12)));
}

for (const asset of manifest.assets) {
  const file = path.join(source, "glb", `${asset.id}.glb`);
  const bytes = await readFile(file);
  const gltf = readGlb(bytes, asset.id);
  assert.equal(gltf.meshes.length, 1, `${asset.id}: one mesh per ingredient`);
  for (const ext of ["EXT_meshopt_compression", "EXT_texture_webp"])
    assert.ok(gltf.extensionsUsed?.includes(ext), `${asset.id}: missing ${ext}`);
  await copyFile(file, path.join(models, `${asset.id}.glb`));
  asset.modelUrl = `/models/texas/${asset.id}.glb`;
  asset.bytes = (await stat(file)).size;
}

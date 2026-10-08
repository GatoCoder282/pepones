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
  for (const material of gltf.materials) {
    const pbr = material.pbrMetallicRoughness;
    assert.ok(pbr.baseColorTexture, `${asset.id}: missing baked color`);
    assert.ok(pbr.metallicRoughnessTexture, `${asset.id}: missing roughness`);
    assert.ok(material.normalTexture, `${asset.id}: missing normal map`);
    assert.ok(material.occlusionTexture, `${asset.id}: missing occlusion`);
  }
  for (const image of gltf.images) {
    assert.ok(Number.isInteger(image.bufferView), "Texture must be embedded");
    assert.equal(image.mimeType, "image/webp", `${asset.id}: textures must be WebP`);
  }
  await copyFile(file, path.join(models, `${asset.id}.glb`));
  asset.modelUrl = `/models/texas/${asset.id}.glb`;
  asset.bytes = (await stat(file)).size;
}

const renders = {};
for (const view of ["front", "three-quarter", "exploded"]) {
  const target = path.join(images, `${view}.webp`);
  const info = await sharp(path.join(source, "renders", `${view}.png`))
    .trim({ threshold: 1 })
    .resize({ width: 1200, height: 1200, fit: "inside", withoutEnlargement: true })
    .webp({ quality: 86, alphaQuality: 90 })
    .toFile(target);
  renders[view] = { src: `/images/texas/${view}.webp`, width: info.width, height: info.height };
}
// The reference photo is shown next to the model and replaces it if WebGL fails.
const photo = await sharp(path.join(root, manifest.referenceFiles[0]))
  .resize({ width: 900, withoutEnlargement: true })
  .webp({ quality: 84 })
  .toFile(path.join(images, "foto-referencia.webp"));

manifest.totalUniqueBytes = manifest.assets.reduce((n, a) => n + a.bytes, 0);
manifest.burgerBytes = manifest.assets
  .filter((a) => a.id !== manifest.side.assetId)
  .reduce((n, a) => n + a.bytes, 0);
manifest.renders = renders;
manifest.photo = { src: "/images/texas/foto-referencia.webp", width: photo.width, height: photo.height };

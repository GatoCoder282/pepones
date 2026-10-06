import { readFile, writeFile, mkdir, copyFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import sharp from "sharp";

const web = fileURLToPath(new URL("../", import.meta.url));
const source = path.resolve(web, "../material/semanal/dona-burger/modelos");
const models = path.join(web, "public/models/dona-burger");
const images = path.join(web, "public/images/dona-burger");
await mkdir(models, { recursive: true });
await mkdir(images, { recursive: true });
const manifest = JSON.parse(
  await readFile(path.join(source, "manifest.json"), "utf8"),
);

for (const asset of manifest.assets) {
  const file = path.join(source, "glb", `${asset.id}.glb`);
  const bytes = await readFile(file);
  assert.equal(
    bytes.toString("ascii", 0, 4),
    "glTF",
    `Invalid GLB: ${asset.id}`,
  );
  assert.equal(bytes.readUInt32LE(4), 2, "Expected glTF 2.0");
  assert.equal(bytes.readUInt32LE(8), bytes.length, "Incomplete GLB");
  const gltf = JSON.parse(
    bytes.toString("utf8", 20, 20 + bytes.readUInt32LE(12)),
  );
  assert.ok(gltf.meshes.length > 0, "Missing mesh");
  for (const material of gltf.materials) {
    assert.ok(
      material.pbrMetallicRoughness.baseColorTexture,
      "Missing baked color",
    );
    assert.ok(
      material.pbrMetallicRoughness.metallicRoughnessTexture,
      "Missing roughness",
    );
    assert.ok(material.normalTexture, "Missing normal map");
  }
  for (const image of gltf.images)
    assert.ok(Number.isInteger(image.bufferView), "Texture must be embedded");
  await copyFile(file, path.join(models, `${asset.id}.glb`));
  asset.modelUrl = `/models/dona-burger/${asset.id}.glb`;
  asset.bytes = (await stat(file)).size;
}
for (const view of ["front", "three-quarter", "exploded"]) {
  await sharp(path.join(source, "renders", `${view}.png`))
    .resize({ width: 1400, withoutEnlargement: true })
    .webp({ quality: 90, alphaQuality: 100 })
    .toFile(path.join(images, `${view}.webp`));
}
manifest.totalUniqueBytes = manifest.assets.reduce((n, a) => n + a.bytes, 0);
await writeFile(
  path.join(models, "manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
);
await writeFile(
  path.join(web, "src/generated/dona-burger.json"),
  JSON.stringify(manifest, null, 2) + "\n",
);
console.log(
  `Dona Burger: ${manifest.assets.length} validated GLBs, ${(manifest.totalUniqueBytes / 1048576).toFixed(1)} MiB, ${manifest.assembledTriangles} triangles.`,
);

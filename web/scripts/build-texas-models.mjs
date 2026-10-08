import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Runs tools/blender/generate_texas.py with the local Blender install.
// Set BLENDER to the executable when it is not in its default location.
const root = fileURLToPath(new URL("../../", import.meta.url));
const defaults = {
  darwin: "/Applications/Blender.app/Contents/MacOS/Blender",
  win32: "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe",
};
const blender = process.env.BLENDER ?? defaults[process.platform] ?? "blender";
if (blender !== "blender" && !existsSync(blender)) {
  console.error(`No se encontró Blender en ${blender}. Define BLENDER con la ruta del ejecutable.`);
  process.exit(1);
}

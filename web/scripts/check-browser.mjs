import { chromium } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import assert from "node:assert/strict";

const browser = await chromium.launch({
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
  headless: true,
  args: [
    "--enable-webgl",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
  ],
});
const errors = [];
const results = [];
mkdirSync("reports", { recursive: true });
async function check(name, work) {
  await work();
  results.push(name);
  console.log("PASS " + name);
}
const page = await browser.newPage({
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 1,
  reducedMotion: "no-preference",
});
page.on("pageerror", (e) => {
  errors.push(e.message);
  console.log("PAGE ERROR", e.message);
});
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(msg.text());
});
await page.goto("http://127.0.0.1:3000/", { waitUntil: "networkidle" });
await check("Inicio: título, demo e imagen cargada", async () => {
  assert.match(await page.title(), /Pepones/);
  assert.equal(
    await page.getByText("EDICIÓN DE DEMOSTRACIÓN", { exact: true }).count(),
    1,
  );
  assert.ok(
    await page
      .locator(".hero-burger")
      .evaluate((img) => img.complete && img.naturalWidth > 0),
  );
});
await page.screenshot({ path: "reports/home-desktop.png", fullPage: false });
await check("Contacto sin teléfono: Instagram y Escape", async () => {
  await page
    .getByRole("button", { name: "Hablemos", exact: true })
    .first()
    .click();
  await page.getByRole("dialog").waitFor();
  assert.equal(
    await page
      .getByRole("link", { name: "Ir a Instagram" })
      .getAttribute("href"),
    "https://www.instagram.com/peponesburger/",
  );
  await page.keyboard.press("Escape");
  assert.equal(await page.locator("dialog[open]").count(), 0);
});
await page.evaluate(() =>
  document
    .querySelector("#ingredientes")
    .scrollIntoView({ behavior: "instant", block: "start" }),
);
await page.waitForTimeout(1500);
await check("Escena 3D inicializada", async () => {
  try {
    await page.locator(".burger-scene canvas").waitFor({ timeout: 10000 });
  } catch (error) {
    console.log("DIAGNOSTICS", JSON.stringify(errors));
    console.log(
      await page.evaluate(async () => ({
        reduced: matchMedia("(prefers-reduced-motion: reduce)").matches,
        canvas: document.querySelectorAll("canvas").length,
        scene: document
          .querySelector(".ingredient-canvas-wrap")
          .innerHTML.slice(0, 1000),
        rect: document
          .querySelector("#ingredientes")
          .getBoundingClientRect()
          .toJSON(),
        webgl: !!document.createElement("canvas").getContext("webgl2"),
        observer: await new Promise((resolve) => {
          const o = new IntersectionObserver(
            ([e]) => {
              resolve({
                intersecting: e.isIntersecting,
                ratio: e.intersectionRatio,
              });
              o.disconnect();
            },
            { rootMargin: "300px" },
          );
          o.observe(document.querySelector("#ingredientes"));
        }),
      })),
    );
    await page.screenshot({ path: "reports/scene-failure.png" });
    throw error;
  }
});
await page.screenshot({ path: "reports/ingredients-desktop.png" });
await check("Scroll reversible y descripción de cada capa", async () => {
  const start = await page
    .locator("#ingredientes")
    .evaluate((el) => el.getBoundingClientRect().top + window.scrollY);
  await page.evaluate(
    (y) => window.scrollTo({ top: y + 1050, behavior: "instant" }),
    start,
  );
  await page.waitForTimeout(1000);
  assert.match(
    await page.locator(".ingredient-side h3").innerText(),
    /Doble queso/,
  );
  await page.screenshot({ path: "reports/ingredients-exploded.png" });
  await page.evaluate(
    (y) => window.scrollTo({ top: y, behavior: "instant" }),
    start,
  );
  await page.waitForTimeout(1000);
  assert.match(
    await page.locator(".ingredient-side h3").innerText(),
    /Todo empieza/,
  );
});
await check("Exploración accesible, selección y cierre", async () => {
  await page
    .getByRole("button", { name: "Explorar ingredientes", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await dialog
    .getByRole("button", { name: "Doble carne", exact: true })
    .click();
  assert.equal(
    await dialog
      .getByRole("button", { name: "Doble carne", exact: true })
      .getAttribute("aria-pressed"),
    "true",
  );
  assert.equal(
    await dialog
      .getByRole("heading", { name: "Doble carne", exact: true })
      .count(),
    1,
  );
  await page.screenshot({ path: "reports/explorer-desktop.png" });
  await dialog.getByRole("button", { name: "Volver a juntar" }).click();
  await page.keyboard.press("Escape");
  assert.equal(await page.locator("dialog[open]").count(), 0);
});
await check("Pérdida de contexto 3D conserva ingredientes", async () => {
  await page
    .locator(".burger-scene canvas")
    .evaluate((canvas) =>
      canvas.dispatchEvent(new Event("webglcontextlost", { cancelable: true })),
    );
  await page.locator(".ingredient-fallback").waitFor();
  await page
    .getByRole("button", { name: "Explorar ingredientes", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Doble queso", exact: true })
    .click();
  assert.equal(
    await page
      .getByRole("dialog")
      .getByRole("heading", { name: "Doble queso" })
      .count(),
    1,
  );
  await page.keyboard.press("Escape");
});
await page.goto("http://127.0.0.1:3000/menu/", { waitUntil: "networkidle" });
await check("Menú: filtro y búsqueda vacía", async () => {
  assert.equal(await page.locator(".menu-card").count(), 8);
  await page.getByRole("button", { name: "El archivo", exact: true }).click();
  assert.equal(await page.locator(".menu-card").count(), 4);
  await page
    .getByRole("textbox", { name: "Buscar hamburguesa o ingrediente" })
    .fill("pepmuffin");
  assert.equal(await page.locator(".menu-card").count(), 1);
  await page.locator(".menu-card").click();
  assert.ok(
    (await page.getByRole("dialog").innerText()).includes(
      "No implica disponibilidad actual",
    ),
  );
  await page.keyboard.press("Escape");
  await page
    .getByRole("textbox", { name: "Buscar hamburguesa o ingrediente" })
    .fill("zzzzzz");
  assert.equal(await page.locator(".menu-card").count(), 0);
  await page.getByRole("button", { name: "Ver todas", exact: true }).click();
  assert.equal(await page.locator(".menu-card").count(), 8);
});
await page.screenshot({ path: "reports/menu-desktop.png", fullPage: true });
await page.goto("http://127.0.0.1:3000/menu/?burger=fugazzeta", {
  waitUntil: "networkidle",
});
await check("Enlace de archivo abre detalle", async () => {
  assert.equal(
    await page
      .getByRole("dialog")
      .getByRole("heading", { name: "Fugazzeta" })
      .count(),
    1,
  );
});
await page.close();
const mobile = await browser.newPage({
  viewport: { width: 390, height: 844 },
  isMobile: true,
  hasTouch: true,
  deviceScaleFactor: 1,
  reducedMotion: "no-preference",
});
mobile.on("pageerror", (e) => errors.push(e.message));
await mobile.goto("http://127.0.0.1:3000/", { waitUntil: "networkidle" });
await check("Móvil sin desbordamiento horizontal", async () => {
  assert.ok(
    await mobile.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  );
});
await mobile.screenshot({ path: "reports/home-mobile.png", fullPage: false });
await check("Navegación móvil", async () => {
  await mobile.getByRole("button", { name: "Abrir navegación" }).click();
  await mobile
    .getByRole("navigation", { name: "Principal móvil" })
    .getByRole("link", { name: "El menú", exact: true })
    .click();
  await mobile.waitForURL("**/menu/");
  assert.equal(await mobile.locator(".menu-card").count(), 8);
});
await mobile.screenshot({ path: "reports/menu-mobile.png", fullPage: true });
await mobile.goto("http://127.0.0.1:3000/");
await mobile.locator("#ingredientes").scrollIntoViewIfNeeded();
await check("Móvil: separar y juntar", async () => {
  await mobile.getByRole("button", { name: "Separar las capas" }).click();
  await mobile.getByRole("button", { name: "Juntar las capas" }).click();
});
await mobile.emulateMedia({ reducedMotion: "reduce" });
await mobile.reload({ waitUntil: "networkidle" });
await check("Movimiento reducido: contenido alternativo", async () => {
  await mobile.locator("#ingredientes").scrollIntoViewIfNeeded();
  assert.equal(await mobile.locator(".ingredient-fallback").count(), 1);
  await mobile
    .getByRole("button", { name: "Explorar ingredientes", exact: true })
    .click();
  await mobile
    .getByRole("dialog")
    .getByRole("button", { name: "Salsa especial" })
    .click();
  assert.equal(
    await mobile
      .getByRole("dialog")
      .getByRole("heading", { name: "Salsa especial" })
      .count(),
    1,
  );
});
await mobile.close();
await browser.close();
writeFileSync(
  "reports/browser-results.json",
  JSON.stringify({ results, errors }, null, 2),
);
assert.deepEqual(errors, [], "Errores de JavaScript o consola");
console.log(
  `${results.length} escenarios comprobados; sin errores de JavaScript.`,
);

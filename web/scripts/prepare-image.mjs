import sharp from "sharp";
const source = "public/images/burger-hero.png";
const metadata = await sharp(source).metadata();
console.log(
  JSON.stringify({
    width: metadata.width,
    height: metadata.height,
    hasAlpha: metadata.hasAlpha,
  }),
);
await sharp(source)
  .resize(1200)
  .webp({ quality: 88 })
  .toFile("public/images/burger-hero.webp");

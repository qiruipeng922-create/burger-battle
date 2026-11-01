// Rasterise the SVG figures to PNG with the bundled sharp/libvips.
// Usage:  NODE_PATH=<bundled node_modules> node render_png.js
const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

(async () => {
  const cands = [path.join(__dirname, "figures"), path.join(__dirname, "..", "figures"), __dirname];
  const dir = cands.find((d) => fs.existsSync(d) && fs.readdirSync(d).some((x) => x.endsWith(".svg"))) || __dirname;
  for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".svg"))) {
    const out = path.join(dir, f.replace(/\.svg$/, ".png"));
    const svg = fs.readFileSync(path.join(dir, f));
    await sharp(svg, { density: 288 }).png().toFile(out);
    const { width, height } = await sharp(out).metadata();
    console.log("wrote", path.basename(out), `${width}x${height}`);
  }
})();

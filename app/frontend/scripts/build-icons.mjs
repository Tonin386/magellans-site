#!/usr/bin/env node
/**
 * Génère app/static/icons.svg : un « sprite » SVG contenant uniquement les icônes
 * utilisées par le site.
 *
 * - icônes Lucide (https://lucide.dev, licence ISC) : {% icon "calendar" %} ;
 * - logos de réseaux sociaux (Simple Icons, licence CC0) : {% icon "brand-instagram" %}.
 *
 * Les noms sont détectés automatiquement dans les gabarits et le code Python,
 * complétés par la liste de icons.safelist.json (icônes choisies dynamiquement).
 */
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const frontend = resolve(here, "..");
const appDir = resolve(frontend, "..");
const output = join(appDir, "static", "icons.svg");
const lucideDir = join(frontend, "node_modules", "lucide-static", "icons");
const simpleIconsDir = join(frontend, "node_modules", "simple-icons", "icons");

// Logos absents de Simple Icons : tracés maison.
const CUSTOM_BRANDS = {
  linkedin:
    '<path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.78 2.65 4.78 6.1V21h-4v-5.5c0-1.3-.02-3-1.83-3-1.83 0-2.11 1.43-2.11 2.9V21H9z"/>',
};

const PATTERNS = [
  /\{%\s*icon\s+["']([a-z0-9-]+)["']/g, // {% icon "name" %}
  /\bicon\s*=\s*["']([a-z0-9-]+)["']/g, // <c-button icon="name">, icon = "name" en Python
  /["']icon["']\s*:\s*["']([a-z0-9-]+)["']/g, // {"icon": "name"}
  /\bicon\(\s*["']([a-z0-9-]+)["']/g, // icon("name") en Python
];

function walk(dir, files = []) {
  for (const entry of readdirSync(dir)) {
    if (["node_modules", "dist", "staticfiles", "media", "private", ".venv", "__pycache__", "migrations"].includes(entry)) continue;
    const path = join(dir, entry);
    const stats = statSync(path);
    if (stats.isDirectory()) walk(path, files);
    else if (/\.(html|py)$/.test(entry)) files.push(path);
  }
  return files;
}

const names = new Set(JSON.parse(readFileSync(join(frontend, "icons.safelist.json"), "utf8")));
for (const file of walk(appDir)) {
  const content = readFileSync(file, "utf8");
  for (const pattern of PATTERNS) {
    for (const match of content.matchAll(pattern)) names.add(match[1]);
  }
}

const symbols = [];
const missing = [];
for (const name of [...names].sort()) {
  if (name.startsWith("brand-")) {
    const brand = name.slice(6);
    let inner = CUSTOM_BRANDS[brand];
    if (!inner) {
      try {
        const svg = readFileSync(join(simpleIconsDir, `${brand}.svg`), "utf8");
        inner = svg.replace(/^[\s\S]*?<svg[^>]*>/, "").replace(/<\/svg>\s*$/, "").replace(/<title>.*?<\/title>/, "");
      } catch {
        missing.push(name);
        continue;
      }
    }
    symbols.push(`<symbol id="${name}" viewBox="0 0 24 24"><g fill="currentColor" stroke="none">${inner}</g></symbol>`);
    continue;
  }
  try {
    const svg = readFileSync(join(lucideDir, `${name}.svg`), "utf8");
    const inner = svg
      .replace(/<!--[\s\S]*?-->/g, "")
      .replace(/^[\s\S]*?<svg[^>]*>/, "")
      .replace(/<\/svg>\s*$/, "")
      .replace(/\s+/g, " ")
      .trim();
    symbols.push(`<symbol id="${name}" viewBox="0 0 24 24">${inner}</symbol>`);
  } catch {
    missing.push(name);
  }
}

const sprite =
  '<svg xmlns="http://www.w3.org/2000/svg">\n' +
  "<!-- Généré par frontend/scripts/build-icons.mjs — ne pas modifier à la main. -->\n" +
  "<!-- Icônes : Lucide (ISC) et Simple Icons (CC0). -->\n" +
  symbols.join("\n") +
  "\n</svg>\n";
writeFileSync(output, sprite);
console.log(`icons.svg : ${symbols.length} icônes`);
if (missing.length) {
  console.error(`Icônes introuvables : ${missing.join(", ")}`);
  process.exitCode = 1;
}

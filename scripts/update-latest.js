#!/usr/bin/env node

/**
 * update-latest.js — Copy the latest version's map files to latest/ with fixed mode-prefixed names.
 *
 * Reads manifest.json to find the latest version directory, then copies known
 * texture files to latest/ using a texture-name → mode mapping so URLs never change.
 * Discovered_* textures (Reload/Blitz rotating maps) are saved individually by codename.
 *
 * Run after new version files are committed (triggered by GitHub Action or manually).
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..");

// Known texture → fixed mode alias
const MODE_MAP = {
  Apollo_Terrain_Minimap: "br",
  MiniMapAthena_S08Temp: "og",
};

function main() {
  const manifestPath = path.join(ROOT_DIR, "manifest.json");
  if (!fs.existsSync(manifestPath)) {
    console.error("manifest.json not found — run generate-manifest.js first");
    process.exit(1);
  }

  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  if (!manifest.versions || manifest.versions.length === 0) {
    console.error("No versions in manifest");
    process.exit(1);
  }

  const latest = manifest.versions[0]; // sorted descending by version
  const versionDir = path.join(ROOT_DIR, latest.path);

  if (!fs.existsSync(versionDir)) {
    console.error(`Latest version directory not found: ${versionDir}`);
    process.exit(1);
  }

  console.log(`Latest version: ${latest.version} (${latest.path})`);

  const latestDir = path.join(ROOT_DIR, "latest");
  fs.mkdirSync(latestDir, { recursive: true });

  const files = fs.readdirSync(versionDir);
  let copied = 0;

  for (const file of files) {
    const ext = path.extname(file).toLowerCase();
    if (![".png", ".jpg", ".jpeg"].includes(ext)) continue;

    const baseName = path.basename(file, ext);
    const mode = MODE_MAP[baseName];

    if (mode) {
      // Known mode → fixed-name alias (br_latest.png)
      const destName = `${mode}_latest${ext}`;
      fs.copyFileSync(path.join(versionDir, file), path.join(latestDir, destName));
      console.log(`  ${file} -> latest/${destName}`);
      copied++;
    } else if (/^MiniMapAthena_S\d{2}/i.test(baseName)) {
      // OG mode (Figment seasonal) → og_latest.png (auto-matches any season number)
      const destName = `og_latest${ext}`;
      fs.copyFileSync(path.join(versionDir, file), path.join(latestDir, destName));
      console.log(`  ${file} -> latest/${destName}`);
      copied++;
    } else if (
      baseName.startsWith("Discovered_") ||
      baseName.startsWith("Capture_Iteration_Discovered_")
    ) {
      // Reload/Blitz rotating map → save by codename
      const codename = baseName
        .replace("Capture_Iteration_Discovered_", "")
        .replace("Discovered_", "")
        .toLowerCase();
      const destName = `rotating_${codename}${ext}`;
      fs.copyFileSync(path.join(versionDir, file), path.join(latestDir, destName));
      console.log(`  ${file} -> latest/${destName}`);
      copied++;
    } else {
      // Other textures — copy with original name
      fs.copyFileSync(path.join(versionDir, file), path.join(latestDir, file));
      console.log(`  ${file} -> latest/${file} (unmapped)`);
      copied++;
    }
  }

  // Copy per-mode POI files to stable aliases. Mode keys match generate-manifest.js and the
  // C# extractor: br / og / rotating:<codename>.
  //   pois.json                    -> latest/br_pois.json
  //   pois_og.json                 -> latest/og_pois.json
  //   pois_rotating_<code>.json    -> latest/rotating_<code>_pois.json
  for (const file of files) {
    if (!file.endsWith(".json")) continue;

    let destName = null;
    if (file === "pois.json") destName = "br_pois.json";
    else if (file === "pois_og.json") destName = "og_pois.json";
    else {
      const m = file.match(/^pois_rotating_(.+)\.json$/i);
      if (m) destName = `rotating_${m[1].toLowerCase()}_pois.json`;
    }

    if (destName) {
      fs.copyFileSync(path.join(versionDir, file), path.join(latestDir, destName));
      console.log(`  ${file} -> latest/${destName}`);
    }
  }

  // map_meta.json -> latest/map_meta.json plus per-mode aliases (image dims + world bounds;
  // consumers need these to convert POI world coordinates to pixels).
  const metaFile = path.join(versionDir, "map_meta.json");
  if (fs.existsSync(metaFile)) {
    for (const dest of ["map_meta.json", "br_map_meta.json", "og_map_meta.json"]) {
      fs.copyFileSync(metaFile, path.join(latestDir, dest));
    }
    console.log(`  map_meta.json -> latest/{,br_,og_}map_meta.json`);
  }

  // Copy version-named JSON (e.g. 40_10.json from the old workflow) verbatim.
  for (const file of files) {
    if (!file.endsWith(".json")) continue;
    if (file === "pois.json" || file === "map_meta.json" || /^pois_/i.test(file)) continue;
    if (MODE_MAP[path.basename(file, ".json")]) continue;
    fs.copyFileSync(path.join(versionDir, file), path.join(latestDir, file));
    console.log(`  ${file} -> latest/${file}`);
  }

  console.log(`\nCopied ${copied} map file(s) to latest/`);
}

main();

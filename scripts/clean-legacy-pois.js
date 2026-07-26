#!/usr/bin/env node

/**
 * clean-legacy-pois.js — strip wiki artifacts from the legacy {"locations":[...]} POI files.
 *
 * The pre-extraction archive (everything before 41.20) was scraped from a Fandom wiki, and the
 * scrape captured wiki namespace pages alongside real POI names — entries like
 * "User:DurrrBurger1/Sandbox 18" appear as if they were locations in 25 different versions.
 *
 * This removes only entries that are unambiguously wiki plumbing. It does NOT and cannot make the
 * legacy data complete: those files average 8 locations against a real map's ~15-25, and they carry
 * no coordinates at all. Only 41.20 onward is self-extracted and trustworthy.
 *
 * Usage:  node scripts/clean-legacy-pois.js [--dry-run]
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..");
const DRY = process.argv.includes("--dry-run");

// Wiki namespace prefixes and scrape leftovers. Deliberately narrow: anything that could plausibly
// be a real Fortnite location name is left alone.
const ARTIFACT = /^(User|Category|File|Template|Talk|Special|Help|Module|MediaWiki|Project):|\/Sandbox\b|^Sandbox \d+$/i;

let filesChanged = 0;
let entriesRemoved = 0;
const removed = new Map();

function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) { walk(full); continue; }
    if (!name.endsWith(".json")) continue;

    let text;
    try { text = fs.readFileSync(full, "utf8"); } catch { continue; }
    if (!text.trimStart().startsWith("{")) continue;

    let data;
    try { data = JSON.parse(text); } catch { continue; }
    if (!Array.isArray(data.locations)) continue;

    const before = data.locations.length;
    const kept = data.locations.filter(l => {
      const isArtifact = typeof l !== "string" || !l.trim() || ARTIFACT.test(l.trim());
      if (isArtifact) removed.set(l, (removed.get(l) || 0) + 1);
      return !isArtifact;
    });
    if (kept.length === before) continue;

    entriesRemoved += before - kept.length;
    filesChanged++;
    data.locations = kept;
    if (!DRY) fs.writeFileSync(full, JSON.stringify(data, null, 2));
  }
}

for (const entry of fs.readdirSync(ROOT_DIR)) {
  if (entry.startsWith("chapter_")) walk(path.join(ROOT_DIR, entry));
}

console.log(`${DRY ? "[dry-run] " : ""}cleaned ${entriesRemoved} artifact entr(ies) from ${filesChanged} file(s)`);
for (const [name, n] of [...removed.entries()].sort((a, b) => b[1] - a[1])) {
  console.log(`   ${String(n).padStart(3)}x  ${name}`);
}

#!/usr/bin/env node

/**
 * Generate manifest.json for fortnite-archives
 * Walks the directory tree and produces a structured manifest of all map versions.
 * Handles both naming formats: 3-part (1_6_0) and 2-part (33_00)
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..");

// Version range to chapter/season mapping
const VERSION_TO_CHAPTER_SEASON = [
  // Chapter 1
  { minVersion: 1.0, maxVersion: 1.11, chapter: 1, season: 1 },
  { minVersion: 2.0, maxVersion: 2.5, chapter: 1, season: 2 },
  { minVersion: 3.0, maxVersion: 3.6, chapter: 1, season: 3 },
  { minVersion: 4.0, maxVersion: 4.5, chapter: 1, season: 4 },
  { minVersion: 5.0, maxVersion: 5.41, chapter: 1, season: 5 },
  { minVersion: 6.0, maxVersion: 6.31, chapter: 1, season: 6 },
  { minVersion: 7.0, maxVersion: 7.40, chapter: 1, season: 7 },
  { minVersion: 8.0, maxVersion: 8.51, chapter: 1, season: 8 },
  { minVersion: 9.0, maxVersion: 9.41, chapter: 1, season: 9 },
  { minVersion: 10.0, maxVersion: 10.40, chapter: 1, season: 10 },
  // Chapter 2
  { minVersion: 11.0, maxVersion: 11.50, chapter: 2, season: 1 },
  { minVersion: 12.0, maxVersion: 12.61, chapter: 2, season: 2 },
  { minVersion: 13.0, maxVersion: 13.40, chapter: 2, season: 3 },
  { minVersion: 14.0, maxVersion: 14.60, chapter: 2, season: 4 },
  { minVersion: 15.0, maxVersion: 15.50, chapter: 2, season: 5 },
  { minVersion: 16.0, maxVersion: 16.50, chapter: 2, season: 6 },
  { minVersion: 17.0, maxVersion: 17.50, chapter: 2, season: 7 },
  { minVersion: 18.0, maxVersion: 18.40, chapter: 2, season: 8 },
  // Chapter 3
  { minVersion: 19.0, maxVersion: 19.40, chapter: 3, season: 1 },
  { minVersion: 20.0, maxVersion: 20.40, chapter: 3, season: 2 },
  { minVersion: 21.0, maxVersion: 21.51, chapter: 3, season: 3 },
  { minVersion: 22.0, maxVersion: 22.40, chapter: 3, season: 4 },
  // Chapter 4
  { minVersion: 23.0, maxVersion: 23.50, chapter: 4, season: 1 },
  { minVersion: 24.0, maxVersion: 24.40, chapter: 4, season: 2 },
  { minVersion: 25.0, maxVersion: 25.30, chapter: 4, season: 3 },
  { minVersion: 26.0, maxVersion: 26.30, chapter: 4, season: 4 },
  { minVersion: 27.0, maxVersion: 27.11, chapter: 4, season: 5 },
  // Chapter 5
  { minVersion: 28.0, maxVersion: 28.30, chapter: 5, season: 1 },
  { minVersion: 29.0, maxVersion: 29.40, chapter: 5, season: 2 },
  { minVersion: 30.0, maxVersion: 30.30, chapter: 5, season: 3 },
  { minVersion: 31.0, maxVersion: 31.40, chapter: 5, season: 4 },
  // Chapter 6
  { minVersion: 32.0, maxVersion: 32.11, chapter: 6, season: 0 }, // OG
  { minVersion: 33.0, maxVersion: 33.40, chapter: 6, season: 1 },
  { minVersion: 34.0, maxVersion: 34.40, chapter: 6, season: 2 },
  { minVersion: 35.0, maxVersion: 35.40, chapter: 6, season: 3 },
  { minVersion: 36.0, maxVersion: 37.99, chapter: 6, season: 4 },
  { minVersion: 38.0, maxVersion: 38.99, chapter: 6, season: 5 },
];

/**
 * Parse a folder/file version string like "1_6_0", "33_00", "38_10" into a numeric version.
 * Also handles suffixed names like "13_20-(water-lvl-4)", "27_00-stage-2", "32-week-2"
 */
function parseVersion(versionStr) {
  // Strip any suffix after the version part (e.g., "13_20-(water-lvl-4)" -> "13_20")
  const cleaned = versionStr.replace(/[-(].*$/, "").replace(/-$/, "");
  const parts = cleaned.split("_").map(Number);

  if (parts.some(isNaN)) return null;

  if (parts.length === 3) {
    // Old format: major_minor_patch (e.g., 1_6_0)
    return parts[0] + parts[1] / 100 + parts[2] / 10000;
  } else if (parts.length === 2) {
    // New format: major_minor (e.g., 33_00)
    return parts[0] + parts[1] / 100;
  } else if (parts.length === 1) {
    // Single number (e.g., "32" from "32-week-2")
    return parts[0];
  }
  return null;
}

/**
 * Convert folder name to display string (e.g., "33_00" -> "33.00", "13_20-(water-lvl-4)" -> "13.20-(water-lvl-4)")
 */
function versionToDisplay(versionStr) {
  // Replace only the first underscore-separated version part, keep suffix
  return versionStr.replace(/_/g, ".");
}

/**
 * Look up chapter/season for a version number
 */
function getChapterSeason(numericVersion) {
  for (const entry of VERSION_TO_CHAPTER_SEASON) {
    if (numericVersion >= entry.minVersion && numericVersion <= entry.maxVersion) {
      return { chapter: entry.chapter, season: entry.season };
    }
  }
  return { chapter: null, season: null };
}

/**
 * Walk the directory tree to find all version folders
 */
function findVersions() {
  const versions = [];
  const warnings = [];

  // Walk chapter_X/season_Y directories
  const entries = fs.readdirSync(ROOT_DIR);

  for (const chapterDir of entries) {
    if (!chapterDir.startsWith("chapter_")) continue;
    const chapterPath = path.join(ROOT_DIR, chapterDir);
    if (!fs.statSync(chapterPath).isDirectory()) continue;

    const chapterNum = parseInt(chapterDir.split("_")[1]);

    const seasonDirs = fs.readdirSync(chapterPath);
    for (const seasonDir of seasonDirs) {
      if (!seasonDir.startsWith("season_")) continue;
      const seasonPath = path.join(chapterPath, seasonDir);
      if (!fs.statSync(seasonPath).isDirectory()) continue;

      const seasonNum = parseInt(seasonDir.split("_")[1]);

      // Each version folder inside season
      const versionDirs = fs.readdirSync(seasonPath);
      for (const versionDir of versionDirs) {
        const versionPath = path.join(seasonPath, versionDir);
        if (!fs.statSync(versionPath).isDirectory()) continue;

        const relativePath = `${chapterDir}/${seasonDir}/${versionDir}`;
        const numericVersion = parseVersion(versionDir);

        if (numericVersion === null) {
          warnings.push(`Skipping unrecognized folder: ${relativePath}`);
          continue;
        }

        // Look for map image (JPG/PNG)
        const files = fs.readdirSync(versionPath);
        const mapFile = files.find(f => /\.(jpg|jpeg|png)$/i.test(f));
        const poisFile = files.find(f => /\.json$/i.test(f));

        // Check for mismatched files
        if (mapFile) {
          const mapBaseName = path.basename(mapFile, path.extname(mapFile));
          if (mapBaseName !== versionDir) {
            warnings.push(`Mismatched map file: ${relativePath}/${mapFile} (expected ${versionDir}.*)`);
          }
        }
        if (poisFile) {
          const poisBaseName = path.basename(poisFile, ".json");
          if (poisBaseName !== versionDir) {
            warnings.push(`Mismatched POI file: ${relativePath}/${poisFile} (expected ${versionDir}.json)`);
          }
        }

        // Use folder-based chapter/season (most reliable since the user organized the data)
        versions.push({
          version: versionToDisplay(versionDir),
          chapter: chapterNum,
          season: seasonNum,
          path: relativePath,
          hasMap: !!mapFile,
          hasPois: !!poisFile,
          mapFile: mapFile || null,
          poisFile: poisFile || null,
        });
      }
    }
  }

  // Also check a "latest" symlink/folder
  const latestPath = path.join(ROOT_DIR, "latest");
  if (fs.existsSync(latestPath)) {
    // latest is typically a symlink or copy — we don't add it to versions
  }

  // Sort by numeric version descending
  versions.sort((a, b) => {
    const aNum = parseVersion(a.version.replace(/\./g, "_")) || 0;
    const bNum = parseVersion(b.version.replace(/\./g, "_")) || 0;
    return bNum - aNum;
  });

  return { versions, warnings };
}

// Main
const { versions, warnings } = findVersions();

if (warnings.length > 0) {
  console.warn("\n=== WARNINGS ===");
  warnings.forEach(w => console.warn(`  ⚠️  ${w}`));
  console.warn("");
}

const latestVersion = versions.length > 0 ? versions[0].version : null;

const manifest = {
  generated: new Date().toISOString(),
  latest: latestVersion,
  count: versions.length,
  versions,
};

const outputPath = path.join(ROOT_DIR, "manifest.json");
fs.writeFileSync(outputPath, JSON.stringify(manifest, null, 2));

console.log(`✅ Generated manifest.json with ${versions.length} versions`);
console.log(`   Latest: ${latestVersion}`);
console.log(`   Output: ${outputPath}`);
if (warnings.length > 0) {
  console.log(`   ⚠️  ${warnings.length} warnings (see above)`);
}

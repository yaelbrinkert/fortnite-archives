#!/bin/bash
# Download map images from fortnite.gg for missing/wrong versions
# Usage: bash scripts/scrape-fortnite-gg.sh [--all] [--dry-run]
#
# By default, only downloads versions that are missing or known-duplicate.
# --all: re-download ALL versions (overwrites existing)
# --dry-run: show what would be downloaded without actually downloading

set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="https://fortnite.gg/img/maps"

ALL=false
DRY_RUN=false
for arg in "$@"; do
  case $arg in
    --all) ALL=true ;;
    --dry-run) DRY_RUN=true ;;
  esac
done

# Version → chapter, season mapping
declare -A VERSION_MAP=(
  # Chapter 6, Season 4
  ["37.10"]="chapter_6/season_4"
  ["37.20"]="chapter_6/season_4"
  # Chapter 6, Season 5
  ["38.00"]="chapter_6/season_5"
  ["38.11"]="chapter_6/season_5"
  # Chapter 7, Season 1
  ["39.00"]="chapter_7/season_1"
  ["39.10"]="chapter_7/season_1"
  ["39.11"]="chapter_7/season_1"
  ["39.20"]="chapter_7/season_1"
  ["39.30"]="chapter_7/season_1"
)

# Versions that exist but are known duplicates (should be re-downloaded)
KNOWN_DUPLICATES=("39.50" "39.51" "40.00")

# All versions available on fortnite.gg (from our scan)
ALL_VERSIONS=(
  "37.00" "37.10" "37.20" "37.40" "37.50"
  "38.00" "38.10" "38.11"
  "39.00" "39.10" "39.11" "39.20" "39.30" "39.40" "39.50" "39.51"
  "40.00"
)

# Existing version → directory mapping (for versions already in the archive)
declare -A EXISTING_MAP=(
  ["37.00"]="chapter_6/season_4"
  ["37.40"]="chapter_6/season_4"
  ["37.50"]="chapter_6/season_4"
  ["38.10"]="chapter_6/season_5"
  ["39.40"]="chapter_7/season_1"
  ["39.50"]="chapter_7/season_1"
  ["39.51"]="chapter_7/season_1"
  ["40.00"]="chapter_7/season_2"
)

download_version() {
  local version="$1"
  local dir_name="${version//./_}"  # 38.00 → 38_00

  # Determine target directory
  local rel_dir=""
  if [[ -n "${VERSION_MAP[$version]+x}" ]]; then
    rel_dir="${VERSION_MAP[$version]}"
  elif [[ -n "${EXISTING_MAP[$version]+x}" ]]; then
    rel_dir="${EXISTING_MAP[$version]}"
  else
    echo "  SKIP $version (no directory mapping)"
    return
  fi

  local target_dir="$BASE_DIR/$rel_dir/$dir_name"
  local target_file="$target_dir/${dir_name}.jpg"
  local url="$BASE_URL/$version.jpg"

  # Check if we should skip
  if [ "$ALL" = false ] && [ -f "$target_file" ]; then
    # Check if it's a known duplicate
    local is_dup=false
    for dup in "${KNOWN_DUPLICATES[@]}"; do
      if [ "$version" = "$dup" ]; then
        is_dup=true
        break
      fi
    done

    if [ "$is_dup" = false ]; then
      echo "  EXISTS $version → $target_file"
      return
    fi
    echo "  REPLACE $version (known duplicate)"
  fi

  if [ "$DRY_RUN" = true ]; then
    echo "  WOULD DOWNLOAD $url → $target_file"
    return
  fi

  mkdir -p "$target_dir"

  local http_code
  http_code=$(curl -s -w "%{http_code}" -o "$target_file" "$url" 2>/dev/null)

  if [ "$http_code" = "200" ]; then
    local size
    size=$(stat -c%s "$target_file" 2>/dev/null || stat -f%z "$target_file" 2>/dev/null)
    echo "  OK $version → $target_file ($size bytes)"
  else
    echo "  FAIL $version → HTTP $http_code"
    rm -f "$target_file"
  fi

  # Be polite — small delay between requests
  sleep 0.5
}

echo "=== Fortnite.gg Map Image Scraper ==="
echo "Base dir: $BASE_DIR"
echo "Mode: $([ "$ALL" = true ] && echo 'ALL versions' || echo 'missing/duplicates only')"
echo "$([ "$DRY_RUN" = true ] && echo '(DRY RUN)' || echo '')"
echo ""

for version in "${ALL_VERSIONS[@]}"; do
  download_version "$version"
done

echo ""
echo "Done. Run 'node scripts/generate-manifest.js' to update manifest.json"

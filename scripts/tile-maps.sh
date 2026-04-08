#!/usr/bin/env bash
# tile-maps.sh — Generate Leaflet-compatible TMS tiles for all map modes.
# Deploy to VPS at /home/api-admin/scripts/tile-maps.sh and chmod +x.
#
# Run automatically by api_fortnite_v2 after each successful map SFTP sync,
# or manually: bash /home/api-admin/scripts/tile-maps.sh
#
# Requirements: gdal-bin (sudo apt-get install -y gdal-bin)
# Tile format: TMS raster, zoom 0–5, 256×256 tiles

set -euo pipefail

MAPS_DIR="${MAPS_DIR:-/home/api-admin/fortnite/data/maps}"
TILES_DIR="${TILES_DIR:-/home/api-admin/fortnite/data/tiles}"
ZOOM="${ZOOM:-0-5}"

log() { echo "[tile-maps] $*"; }

# Verify gdal2tiles is available
if ! command -v gdal2tiles.py &>/dev/null && ! command -v gdal2tiles &>/dev/null; then
    echo "[tile-maps] ERROR: gdal2tiles not found. Run: sudo apt-get install -y gdal-bin" >&2
    exit 1
fi

GDAL2TILES=$(command -v gdal2tiles.py 2>/dev/null || command -v gdal2tiles)

tile_image() {
    local src="$1"
    local dest="$2"

    if [ ! -f "$src" ]; then
        log "  SKIP (not found): $src"
        return
    fi

    mkdir -p "$dest"

    # Check if tiles are already up-to-date (compare mtime)
    local xml="$dest/tilemapresource.xml"
    if [ -f "$xml" ] && [ "$xml" -nt "$src" ]; then
        log "  UP-TO-DATE: $dest"
        return
    fi

    log "  Tiling: $src → $dest"
    "$GDAL2TILES" \
        --zoom="$ZOOM" \
        --tilesize=256 \
        --webviewer=none \
        --profile=raster \
        "$src" \
        "$dest/" 2>&1 | sed 's/^/    /'

    log "  Done: $dest"
}

# ── 1. Tile latest/ aliases (one set per active game mode) ──────────────────
log "=== Tiling latest mode maps ==="
LATEST_DIR="$MAPS_DIR/latest"

if [ -d "$LATEST_DIR" ]; then
    for png in "$LATEST_DIR"/*_latest.png "$LATEST_DIR"/rotating_*.png; do
        [ -f "$png" ] || continue
        filename=$(basename "$png" .png)
        # Strip _latest suffix for clean mode name: br_latest → br
        mode="${filename%_latest}"
        tile_image "$png" "$TILES_DIR/$mode/latest"
    done
else
    log "WARNING: latest/ directory not found at $LATEST_DIR"
fi

# ── 2. Tile versioned BR maps (Apollo_Terrain_Minimap.png per version) ───────
log "=== Tiling versioned BR maps ==="

for chapter_dir in "$MAPS_DIR"/chapter_*/; do
    [ -d "$chapter_dir" ] || continue
    chapter=$(basename "$chapter_dir")

    for season_dir in "$chapter_dir"season_*/; do
        [ -d "$season_dir" ] || continue

        for version_dir in "$season_dir"*/; do
            [ -d "$version_dir" ] || continue
            version=$(basename "$version_dir")

            br_png="$version_dir/Apollo_Terrain_Minimap.png"
            tile_dir="$TILES_DIR/br/$version"

            # Only tile if not done yet
            if [ ! -f "$tile_dir/tilemapresource.xml" ]; then
                tile_image "$br_png" "$tile_dir"
            fi
        done
    done
done

log "=== All tiling complete ==="

#!/usr/bin/env bash
# setup-vps-tiles.sh — One-time VPS setup for tile generation + Caddy serving.
# Run once on your VPS: bash setup-vps-tiles.sh
#
# What this does:
#   1. Install gdal-bin (for gdal2tiles)
#   2. Create the tiles directory
#   3. Deploy tile-maps.sh to /home/api-admin/scripts/
#   4. Print the Caddy config snippet to add

set -euo pipefail

SCRIPTS_DIR="/home/api-admin/scripts"
TILES_DIR="/home/api-admin/fortnite/data/tiles"

echo "=== Installing GDAL ==="
sudo apt-get update -qq
sudo apt-get install -y gdal-bin
gdal2tiles.py --version || gdal2tiles --version

echo "=== Creating directories ==="
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$TILES_DIR"

echo "=== Deploying tile-maps.sh ==="
# Copy this script's sibling tile-maps.sh to the VPS scripts dir
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/tile-maps.sh" "$SCRIPTS_DIR/tile-maps.sh"
chmod +x "$SCRIPTS_DIR/tile-maps.sh"

echo "=== Running initial tile generation (this may take a few minutes) ==="
bash "$SCRIPTS_DIR/tile-maps.sh"

echo ""
echo "=== DONE ==="
echo ""
echo "Add this block to your Caddyfile to serve tiles:"
echo ""
echo "  # Tile map static files"
echo "  route /tiles/* {"
echo "      uri strip_prefix /tiles"
echo "      root * $TILES_DIR"
echo "      file_server"
echo "      header Cache-Control \"public, max-age=86400\""
echo "  }"
echo ""
echo "Tiles will be available at: https://api-fortnite.com/tiles/{mode}/{version}/{z}/{x}/{y}.png"
echo "  e.g. https://api-fortnite.com/tiles/br/latest/5/4/3.png"
echo "  e.g. https://api-fortnite.com/tiles/br/40_10/5/4/3.png"
echo ""
echo "Update page.tsx TILE_BASE to use this URL instead of GitHub raw."

#!/usr/bin/env bash
# TOKNNews safe deploy: repo → live (no deletes, no data/logs copied)

set -euo pipefail

SRC="/var/www/toknnews-repo"
DEST="/var/www/toknnews-live"

echo "[TOKNNews] Safe deploy from $SRC → $DEST"

# Optional dry-run: ./deployment.sh --dry-run
RSYNC_FLAGS=""
if [[ "${1:-}" == "--dry-run" ]]; then
  RSYNC_FLAGS="--dry-run --progress"
  echo "[TOKNNews] DRY RUN — no changes will be made"
fi

# Safety check
if [[ ! -d "$SRC" ]]; then
  echo "[ERROR] Source directory not found: $SRC"
  exit 1
fi

# Create destination if missing
mkdir -p "$DEST"

echo
read -r -p "Proceed with sync? [y/N] " ans
if [[ "$ans" != "y" && "$ans" != "Y" ]]; then
  echo "[TOKNNews] Deploy aborted."
  exit 0
fi

rsync -av $RSYNC_FLAGS \
  --exclude ".git/" \
  --exclude ".github/" \
  --exclude "data/" \
  --exclude "logs/" \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  "$SRC"/ "$DEST"/

echo "[TOKNNews] Deploy complete."

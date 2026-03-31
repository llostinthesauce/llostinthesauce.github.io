#!/usr/bin/env bash
# compress.sh — standard image compression for nuBlog
#
# Algorithm: ffmpeg JPEG re-encode
#   -q:v 3        ~90% quality (ffmpeg scale: 1=best, 31=worst)
#   max 2560px    on longest side, preserve aspect ratio
#   skip <200KB   files already small enough
#
# Usage:
#   ./compress.sh                    # process default dirs
#   ./compress.sh images/daily       # process specific dir
#   ./compress.sh --dry-run          # preview only, no changes
#
# Requires: ffmpeg
# Output: overwrites originals in-place (originals backed up with .bak if BACKUP=1)

set -euo pipefail

QUALITY=3
MAX_PX=2560
MIN_BYTES=204800   # 200KB — skip files already under this
BACKUP=${BACKUP:-0}
DRY_RUN=0

DEFAULT_DIRS=(
    "images/daily"
    "images/monthly"
    "images/plants"
    "images/galleryhome"
    "images/longformroot"
    "galleries"
)

# Parse args
DIRS=()
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN=1
    else
        DIRS+=("$arg")
    fi
done

if [[ ${#DIRS[@]} -eq 0 ]]; then
    DIRS=("${DEFAULT_DIRS[@]}")
fi

# Require ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "ERROR: ffmpeg not found. Install with: brew install ffmpeg" >&2
    exit 1
fi

COMPRESSED=0
SKIPPED=0
ERRORS=0

process_file() {
    local file="$1"
    local bytes
    bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)

    if (( bytes < MIN_BYTES )); then
        echo "  SKIP  (${bytes}B < ${MIN_BYTES}B)  $file"
        (( SKIPPED++ )) || true
        return
    fi

    local ext="${file##*.}"
    local lower_ext
    lower_ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
    local tmp="${file}.tmp.jpg"

    echo "  COMPRESS  (${bytes}B)  $file"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        (( COMPRESSED++ )) || true
        return
    fi

    # ffmpeg: scale so longest side <= MAX_PX, quality -q:v QUALITY
    if ffmpeg -y -loglevel error \
        -i "$file" \
        -vf "scale='if(gt(iw,ih),min(iw,${MAX_PX}),-2)':'if(gt(ih,iw),min(ih,${MAX_PX}),-2)'" \
        -q:v "$QUALITY" \
        "$tmp" 2>/dev/null; then

        local new_bytes
        new_bytes=$(stat -f%z "$tmp" 2>/dev/null || stat -c%s "$tmp" 2>/dev/null || echo 0)

        # Only replace if the compressed version is actually smaller
        if (( new_bytes < bytes )); then
            if [[ "$BACKUP" -eq 1 ]]; then
                cp "$file" "${file}.bak"
            fi
            mv "$tmp" "$file"
            echo "         → ${new_bytes}B (saved $(( bytes - new_bytes ))B)"
            (( COMPRESSED++ )) || true
        else
            rm -f "$tmp"
            echo "         → already optimal, skipping"
            (( SKIPPED++ )) || true
        fi
    else
        rm -f "$tmp"
        echo "  ERROR  $file"
        (( ERRORS++ )) || true
    fi
}

echo "=== nuBlog image compression ==="
echo "Settings: quality=${QUALITY}, max=${MAX_PX}px, skip<${MIN_BYTES}B, dry-run=${DRY_RUN}"
echo "Dirs: ${DIRS[*]}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for dir in "${DIRS[@]}"; do
    full_dir="${SCRIPT_DIR}/${dir}"
    if [[ ! -d "$full_dir" ]]; then
        echo "WARNING: directory not found: $full_dir"
        continue
    fi

    echo "--- $dir ---"
    while IFS= read -r -d '' file; do
        process_file "$file"
    done < <(find "$full_dir" -maxdepth 3 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) -print0)
    echo ""
done

echo "=== Done: ${COMPRESSED} compressed, ${SKIPPED} skipped, ${ERRORS} errors ==="

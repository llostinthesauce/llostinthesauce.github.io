#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$ROOT_DIR/images}"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'USAGE'
Usage: ./scripts/strip-image-metadata.sh [path]

Strips location and personal metadata from image files under the target path,
while keeping orientation and color profile data intact.
Defaults to the repo's images/ directory.

Examples:
  ./scripts/strip-image-metadata.sh
  ./scripts/strip-image-metadata.sh /path/to/images
USAGE
  exit 0
fi

if ! command -v exiftool >/dev/null 2>&1; then
  echo "exiftool not found. Install it (brew install exiftool) and retry." >&2
  exit 1
fi

if [[ ! -e "$TARGET" ]]; then
  echo "Target not found: $TARGET" >&2
  exit 1
fi

LOCATION_TAGS=(
  -GPS:all=
  -XMP-iptcCore:Location=
  -XMP-iptcCore:City=
  -XMP-iptcCore:ProvinceState=
  -XMP-iptcCore:CountryName=
  -XMP-iptcCore:CountryCode=
  -XMP-iptcCore:Sublocation=
  -IPTC:City=
  -IPTC:Province-State=
  -IPTC:Country-PrimaryLocationName=
  -IPTC:Country-PrimaryLocationCode=
  -IPTC:Sub-location=
)

PERSONAL_TAGS=(
  -EXIF:Artist=
  -EXIF:Copyright=
  -EXIF:UserComment=
  -EXIF:ImageDescription=
  -EXIF:XPAuthor=
  -EXIF:XPComment=
  -EXIF:XPKeywords=
  -EXIF:XPSubject=
  -EXIF:OwnerName=
  -EXIF:SerialNumber=
  -EXIF:BodySerialNumber=
  -EXIF:LensSerialNumber=
  -EXIF:ImageUniqueID=
  -XMP:Creator=
  -XMP:CreatorTool=
  -XMP:CreatorContactInfo=
  -XMP:Rights=
  -XMP:Description=
  -XMP:Title=
  -XMP:Subject=
  -XMP:PersonInImage=
  -XMP:RegionInfo=
  -IPTC:By-line=
  -IPTC:By-lineTitle=
  -IPTC:Credit=
  -IPTC:Source=
  -IPTC:Contact=
  -IPTC:CopyrightNotice=
)

strip_metadata() {
  local path="$1"
  exiftool \
    -P \
    -overwrite_original \
    -m \
    -q -q \
    "${LOCATION_TAGS[@]}" \
    "${PERSONAL_TAGS[@]}" \
    "$path"
}

strip_png_ico() {
  local ico_path="$1"
  local tmp_path="${ico_path}.tmp.png"

  cp "$ico_path" "$tmp_path"
  strip_metadata "$tmp_path"
  mv "$tmp_path" "$ico_path"
}

echo "Stripping metadata from images under: $TARGET"

if [[ -f "$TARGET" ]]; then
  if [[ "$TARGET" == *.ico ]]; then
    if file "$TARGET" | grep -qi 'PNG image data'; then
      strip_png_ico "$TARGET"
    else
      echo "Skipping unsupported ICO file: $TARGET"
    fi
  else
    strip_metadata "$TARGET"
  fi
else
  exiftool \
    -r \
    -P \
    -overwrite_original \
    -m \
    -q -q \
    "${LOCATION_TAGS[@]}" \
    "${PERSONAL_TAGS[@]}" \
    -ext jpg -ext jpeg -ext png -ext gif -ext webp -ext heic -ext heif -ext tif -ext tiff -ext bmp \
    "$TARGET"

  while IFS= read -r -d '' ico_path; do
    if file "$ico_path" | grep -qi 'PNG image data'; then
      strip_png_ico "$ico_path"
    else
      echo "Skipping unsupported ICO file: $ico_path"
    fi
  done < <(find "$TARGET" -type f -iname '*.ico' -print0)
fi

echo "Done."

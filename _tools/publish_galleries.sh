#!/bin/bash

# ==============================================================================
# Gallery Publisher Script
# Automatically ingests photos from a local drop folder, resizes them,
# generates the HTML gallery page, updates the gallery data, and pushes to git.
# ==============================================================================

# Configuration
INCOMING_PLANTS="_incoming_photos/plants"
INCOMING_MONTHLY="_incoming_photos/monthly"

# Determine the time-based labels for the gallery
MONTH_YEAR=$(date +"%b%Y" | tr '[:upper:]' '[:lower:]')  # e.g., mar2026
MONTH_LABEL=$(date +"%b %Y" | tr '[:upper:]' '[:lower:]') # e.g., mar 2026
MONTH_SHORT=$(date +"%b" | tr '[:upper:]' '[:lower:]')   # e.g., mar
YEAR=$(date +"%Y")                                       # e.g., 2026
GALLERY_DATA="_tools/gallery-data.js"

# Go to script's directory and then project root just in case
cd "$(dirname "$0")/.."

# Ensure the script is run from the root of the project
if [ ! -f "$GALLERY_DATA" ]; then
    echo "Error: Could not find $GALLERY_DATA. Please run from the project root."
    exit 1
fi

update_gallery_data() {
    local TYPE=$1
    local IMG_PREVIEW=$2
    
    python3 -c "
import sys, re

content = open('$GALLERY_DATA', 'r').read()

if '$TYPE' == 'monthly':
    year_pattern = r\"({\s*label:\s*'\" + '$YEAR' + r\"',\s*className:[^\]]+children:\s*\[)\"
    match = re.search(year_pattern, content)
    if match:
        if \"href: 'images/monthly-images/$MONTH_YEAR.html'\" not in content:
            new_entry = \"\n                    { label: '$MONTH_SHORT', href: 'images/monthly-images/$MONTH_YEAR.html' },\"
            content = content.replace(match.group(1), match.group(1) + new_entry, 1)
            open('$GALLERY_DATA', 'w').write(content)
            print('  -> Updated $GALLERY_DATA for $TYPE')
elif '$TYPE' == 'plants':
    plant_pattern = r\"(title:\s*'plants \+ animals',\s*entries:\s*\[)\"
    match = re.search(plant_pattern, content)
    if match:
        if \"href: 'galleries/plants-$MONTH_YEAR.html'\" not in content:
            new_entry = \"\n            { label: '$MONTH_SHORT $YEAR plants', href: 'galleries/plants-$MONTH_YEAR.html', previewImage: '$IMG_PREVIEW' },\"
            content = content.replace(match.group(1), match.group(1) + new_entry, 1)
            open('$GALLERY_DATA', 'w').write(content)
            print('  -> Updated $GALLERY_DATA for $TYPE')
"
}

process_gallery() {
    local TYPE=$1
    local INCOMING_DIR=$2
    local OUT_IMG_DIR=$3
    local OUT_HTML=$4
    local TITLE=$5
    local CSS_PATH=$6

    shopt -s nullglob
    local images=("$INCOMING_DIR"/*.jpg "$INCOMING_DIR"/*.jpeg "$INCOMING_DIR"/*.png "$INCOMING_DIR"/*.JPG "$INCOMING_DIR"/*.JPEG "$INCOMING_DIR"/*.PNG)
    shopt -u nullglob

    if [ ${#images[@]} -eq 0 ]; then
        echo "No images found in $INCOMING_DIR. Skipping $TYPE."
        return
    fi

    echo "Processing ${#images[@]} images for $TYPE ($MONTH_YEAR)..."
    mkdir -p "$OUT_IMG_DIR"

    local first_img=""
    for img in "${images[@]}"; do
        local filename=$(basename "$img")
        echo "  Moving and resizing $filename..."
        # Resize proportional max dimension 1600px using macOS built-in command
        sips -Z 1600 "$img" > /dev/null 2>&1
        mv "$img" "$OUT_IMG_DIR/"
        if [ -z "$first_img" ]; then
            first_img="$OUT_IMG_DIR/$filename"
        fi
    done

    echo "  Generating HTML: $OUT_HTML..."
    
    shopt -s nullglob
    local final_images=("$OUT_IMG_DIR"/*.jpg "$OUT_IMG_DIR"/*.jpeg "$OUT_IMG_DIR"/*.png "$OUT_IMG_DIR"/*.JPG "$OUT_IMG_DIR"/*.JPEG "$OUT_IMG_DIR"/*.PNG)
    shopt -u nullglob

    cat <<EOF > "$OUT_HTML"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$TITLE - nuBlog</title>
    <link rel="stylesheet" href="$CSS_PATH">
    <link rel="icon" href="../favicon.ico" type="image/x-icon">
    <style>
        .gallery-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }
        .gallery-table td {
            width: 50%;
            padding: 10px;
            text-align: center;
            vertical-align: top;
        }
        .gallery-table img.styled-image {
            max-width: 100%;
            height: auto;
            border: none;
        }
        .gallery-table p {
            margin-top: 5px;
            color: #99CCCC;
            font-size: 0.9em;
        }
    </style>
</head>
<body class="blog-post-page">
    <div class="content">
        <div id="site-header"></div>
        <h1 class="underlined-heading">$TITLE</h1>
        
        <table class="gallery-table">
EOF

    local count=${#final_images[@]}
    for (( i=0; i<count; i+=2 )); do
        echo "            <tr>" >> "$OUT_HTML"
        for (( j=0; j<2; j++ )); do
            local idx=$((i + j))
            if [ $idx -lt $count ]; then
                local img_path="${final_images[$idx]}"
                local img_name=$(basename -- "$img_path")
                local img_name_no_ext="${img_name%.*}"
                
                local rel_img_path=""
                if [[ "$OUT_HTML" == galleries/* ]]; then
                    rel_img_path="../$img_path"
                else
                    rel_img_path="../../$img_path"
                fi
                
                echo "                <td><img src=\"$rel_img_path\" alt=\"$img_name_no_ext\" class=\"styled-image\"><p>$img_name_no_ext</p></td>" >> "$OUT_HTML"
            else
                echo "                <td></td>" >> "$OUT_HTML"
            fi
        done
        echo "            </tr>" >> "$OUT_HTML"
    done

    local js_base=".."
    if [[ "$OUT_HTML" == images/monthly-images/* ]]; then
        js_base="../.."
    fi

    cat <<EOF >> "$OUT_HTML"
        </table>

        <div id="site-footer"></div>
    </div>
    <script src="${js_base}/_tools/include.js" data-base="${js_base}"></script>
</body>
</html>
EOF

    update_gallery_data "$TYPE" "$first_img"
    echo "  Finished processing $TYPE!"
    echo "--------------------------------------------------------"
}

# 1. Process incoming monthly photos
process_gallery "monthly" "$INCOMING_MONTHLY" "images/monthly-images/$MONTH_YEAR" "images/monthly-images/${MONTH_YEAR}.html" "$MONTH_LABEL photos" "../../styles/style.css"

# 2. Process incoming plant photos
process_gallery "plants" "$INCOMING_PLANTS" "images/plants/$MONTH_YEAR" "galleries/plants-${MONTH_YEAR}.html" "$MONTH_LABEL plants" "../styles/style.css"

# 3. Handle Git Operations unless passed the --no-push flag
if [ "$1" != "--no-push" ]; then
    echo "Committing and pushing changes to GitHub..."
    git add images/ galleries/ scripts/
    git commit -m "Auto-generated galleries for $MONTH_LABEL"
    git push
    echo "Done! The updates have been pushed to your repo."
else
    echo "Skipping git push due to --no-push flag."
fi
